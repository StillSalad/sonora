import base64
import json
import uuid
from collections import Counter

from sqlalchemy import select, true
from sqlalchemy.orm import Session

from ..catalog.cards import track_card
from ..catalog.genres import GENRE_LABELS
from ..catalog.visibility import visible_tracks_clause
from ..models import (FeedImpression, Like, PopularityClass, Preview, PreviewStatus, Tag, Track, TrackArtist, TrackTag,
                      User)
from .mixer import WINDOW, Candidate, mix

COUNTRY_NAMES = {"IT": "Italia", "US": "Stati Uniti", "GB": "Regno Unito", "FR": "Francia", "DE": "Germania", "ES": "Spagna"}
POOL_LIMIT = 400


def encode_cursor(session: str) -> str:
    return base64.urlsafe_b64encode(json.dumps({"s": session}).encode()).decode().rstrip("=")


def decode_cursor(cursor: str | None) -> str | None:
    if not cursor:
        return None
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
        s = str(data["s"])
        uuid.UUID(s)
        return s
    except (ValueError, KeyError, TypeError):
        return None


def _taste(db: Session, user: User | None) -> tuple[Counter, set]:
    if not user:
        return Counter(), set()
    liked = select(Like.track_id).where(Like.user_id == user.id)
    genres = Counter(db.scalars(select(Tag.slug).join(TrackTag, TrackTag.tag_id == Tag.id)
                                .where(TrackTag.track_id.in_(liked), Tag.category == "genre")).all())
    artists = set(db.scalars(select(TrackArtist.artist_id).where(TrackArtist.track_id.in_(liked))).all())
    return genres, artists


def _candidates(db: Session, exclude: set, user: User | None) -> tuple[list[Candidate], list[Candidate]]:
    rows = db.execute(select(Track).where(visible_tracks_clause(), Track.id.not_in(exclude) if exclude else true())
                      .order_by(Track.popularity_score.desc().nulls_last(), Track.updated_at.desc()).limit(POOL_LIMIT)).scalars().all()
    if not rows:
        return [], []
    ids = [t.id for t in rows]
    artist_of = dict(db.execute(select(TrackArtist.track_id, TrackArtist.artist_id)
                                .where(TrackArtist.track_id.in_(ids), TrackArtist.role == "primary")).all())
    genres: dict = {}
    for tid, slug in db.execute(select(TrackTag.track_id, Tag.slug).join(Tag, Tag.id == TrackTag.tag_id)
                                .where(TrackTag.track_id.in_(ids), Tag.category == "genre")).all():
        genres.setdefault(tid, []).append(slug)
    playable = set(db.scalars(select(Preview.track_id).where(Preview.track_id.in_(ids),
                                                             Preview.status == PreviewStatus.AVAILABLE)).all())
    liked_genres, liked_artists = _taste(db, user)
    top_genre_total = sum(liked_genres.values()) or 1
    pop, disc = [], []
    for t in rows:
        g = tuple(genres.get(t.id, []))
        aff, reasons = 0.0, []
        if artist_of.get(t.id) in liked_artists:
            aff += 0.35
            reasons.append("Da un artista che hai apprezzato")
        best = max(g, key=lambda s: liked_genres.get(s, 0), default=None)
        if best and liked_genres.get(best):
            aff += 0.4 * liked_genres[best] / top_genre_total
            reasons.append(f"Perché ti piace il genere {GENRE_LABELS.get(best, best)}")
        is_pop = t.popularity_class == PopularityClass.popular
        if is_pop:
            src = (t.popularity_sources or [{}])[0]
            country = COUNTRY_NAMES.get(str(src.get("country", "")).upper(), src.get("country", ""))
            if src.get("rank"):
                reasons.append(f"Popolare in {country}: n. {src['rank']} su Apple Music")
            else:
                reasons.append("Popolare in questo periodo")
            base = (t.popularity_score or 0.5)
        else:
            label = GENRE_LABELS.get(g[0]) if g else None
            reasons.append(f"Scoperta {label} fuori dalle classifiche attuali" if label else "Scoperta fuori dalle classifiche attuali")
            base = 0.5
        base += 0.2 if t.id in playable else 0.0  # chi ha un'anteprima ascoltabile viene prima
        c = Candidate(str(t.id), str(artist_of.get(t.id, t.id)), g, "popular" if is_pop else "discovery", base, aff, reasons)
        (pop if is_pop else disc).append(c)
    return pop, disc


def build_page(db: Session, session: str | None, user: User | None, limit: int, country: str) -> dict:
    session = session or str(uuid.uuid4())
    seen = db.execute(select(FeedImpression).where(FeedImpression.session_id == session)
                      .order_by(FeedImpression.position)).scalars().all()
    exclude = {s.track_id for s in seen}
    pop, disc = _candidates(db, exclude, user)
    # storia recente per diversità artista/genere
    recent_rows = seen[-3:]
    recent: list[Candidate] = []
    for imp in recent_rows:
        art = db.scalar(select(TrackArtist.artist_id).where(TrackArtist.track_id == imp.track_id))
        g = db.scalars(select(Tag.slug).join(TrackTag, TrackTag.tag_id == Tag.id)
                       .where(TrackTag.track_id == imp.track_id, Tag.category == "genre")).all()
        recent.append(Candidate(str(imp.track_id), str(art), tuple(g), imp.slot, 0))
    picked = mix(pop, disc, start=len(seen), count=limit, recent=recent, session=session)
    items = []
    for p in picked:
        track = db.get(Track, uuid.UUID(p.candidate.track_id))
        db.add(FeedImpression(session_id=session, user_id=user.id if user else None, track_id=track.id,
                              position=p.position, slot=p.slot))
        reasons = p.candidate.reasons
        if p.slot == "discovery" and reasons and not reasons[0].startswith("Scoperta"):
            reasons = [r for r in reasons if r.startswith("Scoperta")] + [r for r in reasons if not r.startswith("Scoperta")]
        items.append({"position": p.position, "slot": p.slot, "tolerance": p.tolerance,
                      "explanation": reasons[0] if reasons else None, "reasons": reasons,
                      "track": track_card(db, track, user, country)})
    db.commit()
    window = [s.slot for s in seen] + [p.slot for p in picked]
    window = window[-WINDOW:]
    return {"items": items, "next_cursor": encode_cursor(session) if picked else None,
            "session_id": session, "exhausted": len(picked) < limit,
            "window": {"size": len(window), "popular": window.count("popular"),
                       "discovery": window.count("discovery"), "target": {"popular": 40, "discovery": 10, "of": WINDOW}}}
