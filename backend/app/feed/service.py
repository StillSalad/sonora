import base64
import json
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..catalog.cards import track_card
from ..catalog.genres import GENRE_LABELS
from ..catalog.visibility import visible_tracks_clause
from ..models import (FeedImpression, Like, PopularityClass, Preview, PreviewStatus, Tag, Track, TrackArtist, TrackTag,
                      User)
from .mixer import WINDOW, Candidate, mix

COUNTRY_NAMES = {"IT": "Italia", "US": "Stati Uniti", "GB": "Regno Unito", "FR": "Francia", "DE": "Germania", "ES": "Spagna"}
POOL_LIMIT = 600
HISTORY_DAYS = 14        # memoria tra sessioni
HARD_HOURS = 72          # visti nelle ultime 72 ore: esclusi se c'è abbastanza altra musica
MIN_POOL_FACTOR = 3      # "abbastanza" = almeno 3 volte i brani richiesti nel bacino


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


def _history(db: Session, session: str, user: User | None, device: str | None) -> dict:
    """track_id -> ore dall'ultima volta che è stato mostrato a questa persona (altre sessioni, 14 giorni)."""
    who = []
    if user:
        who.append(FeedImpression.user_id == user.id)
    if device:
        who.append(FeedImpression.device_id == device)
    if not who:
        return {}
    since = datetime.now(timezone.utc) - timedelta(days=HISTORY_DAYS)
    rows = db.execute(select(FeedImpression.track_id, func.max(FeedImpression.created_at))
                      .where(or_(*who), FeedImpression.created_at >= since, FeedImpression.session_id != session)
                      .group_by(FeedImpression.track_id)).all()
    now = datetime.now(timezone.utc)
    out = {}
    for tid, ts in rows:
        ts = ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
        out[tid] = max(0.0, (now - ts).total_seconds() / 3600)
    return out


def _pool_rows(db: Session, exclude: set, popular: bool) -> list[Track]:
    stmt = select(Track).where(visible_tracks_clause())
    if exclude:
        stmt = stmt.where(Track.id.not_in(exclude))
    if popular:
        stmt = stmt.where(Track.popularity_class == PopularityClass.popular)
    else:
        # campione casuale da TUTTO il catalogo, non sempre gli stessi brani
        stmt = stmt.where(Track.popularity_class != PopularityClass.popular).order_by(func.random())
    return db.scalars(stmt.limit(POOL_LIMIT)).all()


def _best_chart(t: Track) -> dict:
    srcs = [x for x in (t.popularity_sources or []) if x.get("rank")]
    if not srcs:
        return {}
    # preferisci la classifica del paese dell'app, poi la posizione migliore
    return sorted(srcs, key=lambda x: (not x.get("home", False), x["rank"]))[0]


def _candidates(db: Session, exclude: set, user: User | None, history: dict, need: int) -> tuple[list[Candidate], list[Candidate]]:
    pools = {"popular": _pool_rows(db, exclude, True), "discovery": _pool_rows(db, exclude, False)}
    rows = pools["popular"] + pools["discovery"]
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
    out: dict[str, list[Candidate]] = {"popular": [], "discovery": []}
    for kind, pool_rows in pools.items():
        fresh = [t for t in pool_rows if history.get(t.id, 1e9) >= HARD_HOURS]
        # se i brani mai sentiti di recente bastano, quelli degli ultimi 3 giorni restano fuori
        usable = fresh if len(fresh) >= need * MIN_POOL_FACTOR else pool_rows
        for t in usable:
            g = tuple(genres.get(t.id, []))
            aff, reasons = 0.0, []
            if artist_of.get(t.id) in liked_artists:
                aff += 0.35
                reasons.append("Da un artista che hai apprezzato")
            best = max(g, key=lambda s: liked_genres.get(s, 0), default=None)
            if best and liked_genres.get(best):
                aff += 0.4 * liked_genres[best] / top_genre_total
                reasons.append(f"Perché ti piace il genere {GENRE_LABELS.get(best, best)}")
            if kind == "popular":
                src = _best_chart(t)
                if src:
                    country = COUNTRY_NAMES.get(str(src.get("country", "")).upper(), src.get("country", ""))
                    reasons.append(f"Popolare in {country}: n. {src['rank']} su Apple Music")
                else:
                    reasons.append("Popolare in questo periodo")
                base = t.popularity_score or 0.5
            else:
                label = GENRE_LABELS.get(g[0]) if g else None
                reasons.append(f"Scoperta {label} fuori dalle classifiche attuali" if label else "Scoperta fuori dalle classifiche attuali")
                base = 0.5
            base += 0.2 if t.id in playable else 0.0  # chi ha un'anteprima ascoltabile viene prima
            hours = history.get(t.id)
            penalty = 0.0
            if hours is not None:
                days = hours / 24
                penalty = 0.9 if hours < HARD_HOURS else 0.6 * max(0.0, 1 - days / HISTORY_DAYS)
            out[kind].append(Candidate(str(t.id), str(artist_of.get(t.id, t.id)), g, kind, base, aff, penalty, reasons))
    return out["popular"], out["discovery"]


def build_page(db: Session, session: str | None, user: User | None, limit: int, country: str,
               device: str | None = None) -> dict:
    session = session or str(uuid.uuid4())
    seen = db.execute(select(FeedImpression).where(FeedImpression.session_id == session)
                      .order_by(FeedImpression.position)).scalars().all()
    exclude = {s.track_id for s in seen}
    history = _history(db, session, user, device)
    pop, disc = _candidates(db, exclude, user, history, limit)
    # storia recente per diversità artista/genere
    recent_rows = seen[-6:]
    recent: list[Candidate] = []
    for imp in recent_rows:
        art = db.scalar(select(TrackArtist.artist_id).where(TrackArtist.track_id == imp.track_id))
        g = db.scalars(select(Tag.slug).join(TrackTag, TrackTag.tag_id == Tag.id)
                       .where(TrackTag.track_id == imp.track_id, Tag.category == "genre")).all()
        recent.append(Candidate(str(imp.track_id), str(art), tuple(g), imp.slot, 0.0))
    picked = mix(pop, disc, start=len(seen), count=limit, recent=recent, session=session)
    items = []
    for p in picked:
        track = db.get(Track, uuid.UUID(p.candidate.track_id))
        db.add(FeedImpression(session_id=session, user_id=user.id if user else None, device_id=device,
                              track_id=track.id, position=p.position, slot=p.slot))
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
