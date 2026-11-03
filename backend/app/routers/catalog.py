import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from ..catalog.cards import preview_view, track_card
from ..catalog.ingest import ingest_track
from ..catalog.normalize import normalize
from ..catalog.visibility import visible_tracks_clause
from ..config import get_settings
from ..db import get_db
from ..errors import ApiError
from ..models import (Album, Artist, Like, Preview, Provider, ProviderTrack, Tag, Track, TrackArtist, TrackTag, User)
from ..providers.base import ProviderUnavailable
from ..providers.registry import get_live_adapter, search_cache
from ..security import current_user, current_user_optional

router = APIRouter(tags=["catalog"])


def _uuid(v: str) -> uuid.UUID:
    try:
        return uuid.UUID(v)
    except ValueError:
        raise ApiError(404, "not_found", "Non trovato.")


def _track(db: Session, track_id: str) -> Track:
    t = db.scalar(select(Track).where(Track.id == _uuid(track_id), visible_tracks_clause()))
    if not t:
        raise ApiError(404, "not_found", "Brano non trovato.")
    return t


@router.get("/tracks/{track_id}")
def get_track(track_id: str, db: Session = Depends(get_db), user: User | None = Depends(current_user_optional)):
    return track_card(db, _track(db, track_id), user, get_settings().store_country)


@router.get("/tracks/{track_id}/availability")
def availability(track_id: str, db: Session = Depends(get_db)):
    t = _track(db, track_id)
    country = get_settings().store_country
    previews = [preview_view(pv, pr, country) | {"rights_reference": pv.rights_reference,
                "last_verified_at": pv.last_verified_at.isoformat() if pv.last_verified_at else None}
                for pv, pr in db.execute(select(Preview, Provider).join(Provider, Provider.id == Preview.provider_id)
                                         .where(Preview.track_id == t.id)).all()]
    links = [{"provider": pr.name, "url": pt.external_url, "territory": pt.territory,
              "last_verified_at": pt.last_verified_at.isoformat() if pt.last_verified_at else None}
             for pt, pr in db.execute(select(ProviderTrack, Provider).join(Provider, Provider.id == ProviderTrack.provider_id)
                                      .where(ProviderTrack.track_id == t.id)).all()]
    return {"track_id": str(t.id), "country": country.upper(), "previews": previews, "links": links}


@router.get("/artists/{artist_id}")
def get_artist(artist_id: str, db: Session = Depends(get_db), user: User | None = Depends(current_user_optional)):
    a = db.get(Artist, _uuid(artist_id))
    if not a:
        raise ApiError(404, "not_found", "Artista non trovato.")
    tracks = db.scalars(select(Track).join(TrackArtist, TrackArtist.track_id == Track.id)
                        .where(TrackArtist.artist_id == a.id, visible_tracks_clause())
                        .order_by(Track.popularity_score.desc().nulls_last()).limit(30)).all()
    c = get_settings().store_country
    return {"id": str(a.id), "name": a.canonical_name, "tracks": [track_card(db, t, user, c) for t in tracks]}


@router.get("/albums/{album_id}")
def get_album(album_id: str, db: Session = Depends(get_db), user: User | None = Depends(current_user_optional)):
    al = db.get(Album, _uuid(album_id))
    if not al:
        raise ApiError(404, "not_found", "Album non trovato.")
    tracks = db.scalars(select(Track).where(Track.album_id == al.id, visible_tracks_clause())).all()
    c = get_settings().store_country
    return {"id": str(al.id), "title": al.title, "release_date": al.release_date.isoformat() if al.release_date else None,
            "artwork_url": al.artwork_url, "tracks": [track_card(db, t, user, c) for t in tracks]}


def _search_query(q: str, tags: list[str], tag_mode: str, year_from: int | None, year_to: int | None):
    stmt = select(Track).where(visible_tracks_clause())
    if q:
        n = f"%{normalize(q)}%"
        artist_match = select(TrackArtist.track_id).join(Artist, Artist.id == TrackArtist.artist_id).where(Artist.sort_name.like(n))
        album_match = select(Album.id).where(func.lower(Album.title).like(f"%{q.lower()}%"))
        stmt = stmt.where(or_(Track.normalized_title.like(n), Track.id.in_(artist_match), Track.album_id.in_(album_match)))
    if tags:
        tag_ids = select(Tag.id).where(Tag.slug.in_(tags))
        if tag_mode == "and":
            stmt = stmt.where(and_(*[Track.id.in_(select(TrackTag.track_id).join(Tag, Tag.id == TrackTag.tag_id)
                                                  .where(Tag.slug == s)) for s in tags]))
        else:
            stmt = stmt.where(Track.id.in_(select(TrackTag.track_id).where(TrackTag.tag_id.in_(tag_ids))))
    if year_from:
        stmt = stmt.where(Track.release_date >= date(year_from, 1, 1))
    if year_to:
        stmt = stmt.where(Track.release_date <= date(year_to, 12, 31))
    return stmt.order_by(Track.popularity_score.desc().nulls_last(), Track.title)


@router.get("/search")
def search(q: str = Query("", max_length=100), tags: str = "", tag_mode: str = Query("and", pattern="^(and|or)$"),
           year_from: int | None = Query(None, ge=1900, le=2100), year_to: int | None = Query(None, ge=1900, le=2100),
           limit: int = Query(20, ge=1, le=50), live: bool = True,
           db: Session = Depends(get_db), user: User | None = Depends(current_user_optional),
           adapter=Depends(get_live_adapter)):
    q = q.strip()
    tag_list = [t for t in tags.split(",") if t][:5]
    if not q and not tag_list:
        raise ApiError(422, "empty_query", "Scrivi qualcosa da cercare o scegli un tag.")
    stmt = _search_query(q, tag_list, tag_mode, year_from, year_to)
    results = db.scalars(stmt.limit(limit)).all()
    live_status = "skipped"
    if q and live and len(results) < limit:
        key = f"{get_settings().store_country}:{normalize(q)}"
        if adapter is None:
            live_status = "disabled"
        elif search_cache.fresh(key):
            live_status = "cached"
        else:
            try:
                for ext in adapter.search_tracks(q, limit=25):
                    ingest_track(db, ext)
                db.commit()
                search_cache.mark(key)
                live_status = "ok"
                results = db.scalars(stmt.limit(limit)).all()
            except ProviderUnavailable:
                db.rollback()
                live_status = "unavailable"
    c = get_settings().store_country
    return {"items": [track_card(db, t, user, c) for t in results], "live": live_status}


@router.get("/tags")
def list_tags(category: str | None = None, db: Session = Depends(get_db)):
    stmt = select(Tag, func.count(TrackTag.track_id)).outerjoin(
        TrackTag, and_(TrackTag.tag_id == Tag.id, TrackTag.track_id.in_(select(Track.id).where(visible_tracks_clause())))
    ).where(Tag.status == "active").group_by(Tag.id).order_by(Tag.category, Tag.slug)
    if category:
        stmt = stmt.where(Tag.category == category)
    return {"items": [{"slug": t.slug, "label": t.label, "category": t.category, "origin": t.origin.value,
                       "track_count": n} for t, n in db.execute(stmt).all()]}


@router.get("/tags/{slug}/tracks")
def tag_tracks(slug: str, category: str = Query("genre", pattern="^(genre|mood)$"), offset: int = Query(0, ge=0),
               limit: int = Query(20, ge=1, le=50), db: Session = Depends(get_db),
               user: User | None = Depends(current_user_optional)):
    tag = db.scalar(select(Tag).where(Tag.slug == slug, Tag.category == category))
    if not tag:
        raise ApiError(404, "not_found", "Tag non trovato.")
    tracks = db.scalars(select(Track).join(TrackTag, TrackTag.track_id == Track.id)
                        .where(TrackTag.tag_id == tag.id, visible_tracks_clause())
                        .order_by(Track.popularity_score.desc().nulls_last(), Track.title).offset(offset).limit(limit + 1)).all()
    c = get_settings().store_country
    return {"tag": {"slug": tag.slug, "label": tag.label, "category": tag.category},
            "items": [track_card(db, t, user, c) for t in tracks[:limit]],
            "next_offset": offset + limit if len(tracks) > limit else None}


@router.post("/tracks/{track_id}/like", status_code=204)
def like(track_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    t = _track(db, track_id)
    if not db.get(Like, (user.id, t.id)):
        db.add(Like(user_id=user.id, track_id=t.id))
        db.commit()


@router.delete("/tracks/{track_id}/like", status_code=204)
def unlike(track_id: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    lk = db.get(Like, (user.id, _uuid(track_id)))
    if lk:
        db.delete(lk)
        db.commit()


@router.get("/me/likes")
def my_likes(db: Session = Depends(get_db), user: User = Depends(current_user)):
    tracks = db.scalars(select(Track).join(Like, Like.track_id == Track.id).where(Like.user_id == user.id)
                        .order_by(Like.created_at.desc()).limit(200)).all()
    c = get_settings().store_country
    return {"items": [track_card(db, t, user, c) for t in tracks]}

