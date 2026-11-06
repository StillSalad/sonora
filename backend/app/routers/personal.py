"""Scelta iniziale di generi e artisti, brani simili, voti sui mood."""
import random
import uuid

from fastapi import APIRouter, Depends, Header, Query
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..catalog.cards import track_card
from ..catalog.genres import GENRE_LABELS, MOOD_LABELS
from ..catalog.visibility import visible_tracks_clause
from ..config import get_settings
from ..db import get_db
from ..errors import ApiError
from ..feed.personal import MAX_ARTISTS, MAX_GENRES, negatives, valid_device
from ..models import (Album, Artist, MoodVote, Tag, TagOrigin, Track, TrackArtist, TrackTag, User,
                      UserPreference)
from ..security import current_user, current_user_optional

router = APIRouter(tags=["personal"])


# ---------- preferenze esplicite ----------
class PrefsIn(BaseModel):
    genres: list[str] = Field(default_factory=list, max_length=MAX_GENRES)
    artists: list[uuid.UUID] = Field(default_factory=list, max_length=MAX_ARTISTS)


def _prefs_out(db: Session, user: User) -> dict:
    rows = db.execute(select(UserPreference.preference_type, UserPreference.preference_key)
                      .where(UserPreference.user_id == user.id, UserPreference.source == "explicit")).all()
    genres = [k for t, k in rows if t == "genre"]
    ids = [uuid.UUID(k) for t, k in rows if t == "artist"]
    names = dict(db.execute(select(Artist.id, Artist.canonical_name).where(Artist.id.in_(ids))).all()) if ids else {}
    return {"genres": genres, "artists": [{"id": str(i), "name": names[i]} for i in ids if i in names]}


@router.get("/me/preferences")
def get_prefs(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return _prefs_out(db, user)


@router.put("/me/preferences")
def put_prefs(body: PrefsIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    bad = [g for g in body.genres if g not in GENRE_LABELS]
    if bad:
        raise ApiError(422, "invalid_genre", f"Genere non valido: {bad[0]}")
    db.execute(delete(UserPreference).where(UserPreference.user_id == user.id, UserPreference.source == "explicit",
                                            UserPreference.preference_type.in_(["genre", "artist"])))
    for g in dict.fromkeys(body.genres):
        db.add(UserPreference(user_id=user.id, preference_type="genre", preference_key=g, weight=1.0, source="explicit"))
    existing = set(db.scalars(select(Artist.id).where(Artist.id.in_(body.artists))).all()) if body.artists else set()
    for a in dict.fromkeys(body.artists):
        if a in existing:
            db.add(UserPreference(user_id=user.id, preference_type="artist", preference_key=str(a), weight=1.0,
                                  source="explicit"))
    db.commit()
    return _prefs_out(db, user)


@router.get("/onboarding/artists")
def onboarding_artists(genres: str = Query(..., max_length=400), limit: int = Query(30, ge=6, le=60),
                       db: Session = Depends(get_db)):
    """Artisti del catalogo per i generi scelti, i più popolari prima, con la copertina del loro brano migliore."""
    slugs = [g for g in genres.split(",") if g in GENRE_LABELS][:MAX_GENRES]
    if not slugs:
        raise ApiError(422, "invalid_genre", "Scegli almeno un genere.")
    best = (select(TrackArtist.artist_id.label("artist_id"), Tag.slug.label("slug"),
                   func.max(func.coalesce(Track.popularity_score, 0)).label("score"),
                   func.count(Track.id).label("n"))
            .join(Track, Track.id == TrackArtist.track_id).join(TrackTag, TrackTag.track_id == Track.id)
            .join(Tag, Tag.id == TrackTag.tag_id)
            .where(Tag.category == "genre", Tag.slug.in_(slugs), TrackArtist.role == "primary", visible_tracks_clause())
            .group_by(TrackArtist.artist_id, Tag.slug))
    rows = db.execute(best).all()
    by_artist: dict = {}
    for r in rows:
        cur = by_artist.get(r.artist_id)
        if not cur or r.score > cur[0]:
            by_artist[r.artist_id] = (r.score + 0.02 * min(r.n, 10), r.slug)
    # un po' di varietà tra i generi: si alternano i migliori di ciascun genere
    per_genre: dict = {}
    for aid, (score, slug) in sorted(by_artist.items(), key=lambda kv: -kv[1][0]):
        per_genre.setdefault(slug, []).append(aid)
    ordered, i = [], 0
    while len(ordered) < limit and any(i < len(v) for v in per_genre.values()):
        for slug in slugs:
            v = per_genre.get(slug, [])
            if i < len(v):
                ordered.append((v[i], slug))
        i += 1
    ordered = ordered[:limit]
    out = []
    for aid, slug in ordered:
        a = db.get(Artist, aid)
        art = db.scalar(select(Album.artwork_url).join(Track, Track.album_id == Album.id)
                        .join(TrackArtist, TrackArtist.track_id == Track.id)
                        .where(TrackArtist.artist_id == aid, Album.artwork_url.is_not(None), visible_tracks_clause())
                        .order_by(Track.popularity_score.desc().nulls_last()).limit(1))
        out.append({"id": str(aid), "name": a.canonical_name, "genre": slug, "genre_label": GENRE_LABELS[slug],
                    "artwork_url": art})
    return {"items": out}


# ---------- brani simili ----------
@router.get("/tracks/{track_id}/similar")
def similar(track_id: uuid.UUID, limit: int = Query(20, ge=5, le=40), db: Session = Depends(get_db),
            user: User | None = Depends(current_user_optional),
            x_sonora_device: str | None = Header(None, max_length=64)):
    seed = db.scalar(select(Track).where(Track.id == track_id, visible_tracks_clause()))
    if not seed:
        raise ApiError(404, "not_found", "Brano non trovato.")
    neg = negatives(db, user, valid_device(x_sonora_device))
    artist = db.scalar(select(TrackArtist.artist_id).where(TrackArtist.track_id == seed.id, TrackArtist.role == "primary"))
    tag_rows = db.execute(select(Tag.id, Tag.label, Tag.category).join(TrackTag, TrackTag.tag_id == Tag.id)
                          .where(TrackTag.track_id == seed.id)).all()
    picked: list[tuple[Track, str]] = []
    seen = {seed.id} | neg.tracks
    rnd = random.Random()
    overflow: list[tuple[Track, str]] = []  # scartati per il limite di 2 brani per artista
    if artist and artist not in neg.artists:
        same = db.scalars(select(Track).join(TrackArtist, TrackArtist.track_id == Track.id)
                          .where(TrackArtist.artist_id == artist, Track.id.not_in(seen), visible_tracks_clause())
                          .order_by(Track.popularity_score.desc().nulls_last()).limit(3)).all()
        for t in same:
            picked.append((t, "Stesso artista"))
            seen.add(t.id)
    for tag_id, label, cat in sorted(tag_rows, key=lambda r: r.category != "mood"):
        cand = db.execute(select(Track, TrackArtist.artist_id).join(TrackTag, TrackTag.track_id == Track.id)
                          .join(TrackArtist, TrackArtist.track_id == Track.id)
                          .where(TrackTag.tag_id == tag_id, TrackArtist.role == "primary", Track.id.not_in(seen),
                                 visible_tracks_clause()).order_by(func.random()).limit(limit * 3)).all()
        rnd.shuffle(cand)
        per_artist: dict = {}
        for t, aid in cand:
            if aid in neg.artists or t.id in seen:
                continue
            why = f"Stessa atmosfera: {label}" if cat == "mood" else f"Stesso genere: {label}"
            if per_artist.get(aid, 0) >= 2:
                overflow.append((t, why))
                continue
            per_artist[aid] = per_artist.get(aid, 0) + 1
            picked.append((t, why))
            seen.add(t.id)
            if len(picked) >= limit:
                break
        if len(picked) >= limit:
            break
    for t, why in overflow:  # catalogo piccolo: meglio ripetere un artista che dare pochi brani
        if len(picked) >= limit:
            break
        if t.id not in seen:
            picked.append((t, why))
            seen.add(t.id)
    c = get_settings().store_country
    seed_title = seed.title
    items = [{"position": i, "slot": "similar", "tolerance": False, "explanation": why,
              "reasons": [why, f"Simile a “{seed_title}”"], "track": track_card(db, t, user, c)}
             for i, (t, why) in enumerate(picked[:limit])]
    return {"seed": track_card(db, seed, user, c), "items": items}


# ---------- mood votati dalla community ----------
class MoodIn(BaseModel):
    moods: list[str] = Field(default_factory=list, max_length=2)


def _mood_summary(db: Session, track_id: uuid.UUID, user: User | None) -> dict:
    counts = dict(db.execute(select(MoodVote.mood_slug, func.count()).where(MoodVote.track_id == track_id)
                             .group_by(MoodVote.mood_slug)).all())
    voters = db.scalar(select(func.count(func.distinct(MoodVote.user_id))).where(MoodVote.track_id == track_id)) or 0
    mine = set(db.scalars(select(MoodVote.mood_slug).where(MoodVote.track_id == track_id, MoodVote.user_id == user.id)).all()) if user else set()
    return {"voters": voters, "moods": [{"slug": s, "label": MOOD_LABELS[s], "votes": n, "share": round(n / voters, 2)}
                                        for s, n in sorted(counts.items(), key=lambda kv: -kv[1]) if s in MOOD_LABELS],
            "mine": sorted(mine)}


def _recompute_mood_tags(db: Session, track_id: uuid.UUID) -> None:
    """Un mood diventa tag se ha almeno MOOD_MIN_VOTES voti e la maggioranza dei votanti."""
    s = _mood_summary(db, track_id, None)
    keep = {m["slug"]: m["share"] for m in s["moods"]
            if m["votes"] >= get_settings().mood_min_votes and m["share"] >= 0.5}
    tags = {t.slug: t for t in db.scalars(select(Tag).where(Tag.category == "mood")).all()}
    for tt in db.scalars(select(TrackTag).join(Tag, Tag.id == TrackTag.tag_id)
                         .where(TrackTag.track_id == track_id, Tag.category == "mood", TrackTag.source == TagOrigin.user)).all():
        db.delete(tt)
    db.flush()
    for slug, share in keep.items():
        db.add(TrackTag(track_id=track_id, tag_id=tags[slug].id, confidence=share, source=TagOrigin.user))


@router.get("/tracks/{track_id}/moods")
def get_moods(track_id: uuid.UUID, db: Session = Depends(get_db), user: User | None = Depends(current_user_optional)):
    if not db.scalar(select(Track.id).where(Track.id == track_id, visible_tracks_clause())):
        raise ApiError(404, "not_found", "Brano non trovato.")
    return _mood_summary(db, track_id, user)


@router.put("/tracks/{track_id}/moods")
def vote_moods(track_id: uuid.UUID, body: MoodIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not db.scalar(select(Track.id).where(Track.id == track_id, visible_tracks_clause())):
        raise ApiError(404, "not_found", "Brano non trovato.")
    bad = [m for m in body.moods if m not in MOOD_LABELS]
    if bad:
        raise ApiError(422, "invalid_mood", f"Mood non valido: {bad[0]}")
    db.execute(delete(MoodVote).where(MoodVote.track_id == track_id, MoodVote.user_id == user.id))
    for m in dict.fromkeys(body.moods):
        db.add(MoodVote(track_id=track_id, user_id=user.id, mood_slug=m))
    db.flush()
    _recompute_mood_tags(db, track_id)
    db.commit()
    return _mood_summary(db, track_id, user)

