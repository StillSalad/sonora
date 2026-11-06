"""Importa tracce dei provider nel catalogo canonico.

Regole (MASTER_PROMPT §F):
- una traccia esistente del provider viene aggiornata, non duplicata;
- fusione automatica solo con ISRC identico;
- titolo+artista simili e durata entro 2 s => nuova traccia + candidato duplicato da rivedere;
- provenienza e data di verifica salvate per ogni collegamento.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (Album, Artist, DuplicateCandidate, Like, PopularityClass, Preview, PreviewStatus, Provider,
                      ProviderAlbum, ProviderArtist, ProviderTrack, Tag, TagOrigin, Track, TrackArtist, TrackTag)
from ..providers.base import ChartEntry, ExternalTrack
from ..providers import itunes
from .genres import genre_slug
from .normalize import normalize

PREVIEW_TTL = timedelta(days=7)  # gli URL delle anteprime vanno riverificati periodicamente


def now() -> datetime:
    return datetime.now(timezone.utc)


def get_provider(db: Session, name: str) -> Provider:
    p = db.scalar(select(Provider).where(Provider.name == name))
    if not p:
        raise LookupError(f"Provider '{name}' non registrato: esegui 'alembic upgrade head'")
    return p


def _artist(db: Session, provider: Provider, ext: ExternalTrack) -> Artist:
    if ext.artist_external_id:
        link = db.scalar(select(ProviderArtist).where(ProviderArtist.provider_id == provider.id,
                                                      ProviderArtist.external_id == ext.artist_external_id))
        if link:
            link.last_verified_at = now()
            return db.get(Artist, link.artist_id)
    artist = Artist(canonical_name=ext.artist_name, sort_name=normalize(ext.artist_name))
    db.add(artist)
    db.flush()
    if ext.artist_external_id:
        db.add(ProviderArtist(artist_id=artist.id, provider_id=provider.id, external_id=ext.artist_external_id,
                              last_verified_at=now()))
    return artist


def _album(db: Session, provider: Provider, ext: ExternalTrack, artist: Artist) -> Album | None:
    if not ext.album_title:
        return None
    if ext.album_external_id:
        link = db.scalar(select(ProviderAlbum).where(ProviderAlbum.provider_id == provider.id,
                                                     ProviderAlbum.external_id == ext.album_external_id))
        if link:
            album = db.get(Album, link.album_id)
            album.artwork_url = ext.artwork_url or album.artwork_url
            link.last_verified_at = now()
            return album
    album = Album(title=ext.album_title, release_date=ext.release_date, artwork_url=ext.artwork_url,
                  primary_artist_id=artist.id)
    db.add(album)
    db.flush()
    if ext.album_external_id:
        db.add(ProviderAlbum(album_id=album.id, provider_id=provider.id, external_id=ext.album_external_id,
                             last_verified_at=now()))
    return album


def _tag(db: Session, slug: str) -> Tag | None:
    return db.scalar(select(Tag).where(Tag.category == "genre", Tag.slug == slug))


def _preview(db: Session, provider: Provider, track: Track, ext: ExternalTrack) -> None:
    pv = db.scalar(select(Preview).where(Preview.track_id == track.id, Preview.provider_id == provider.id))
    if not pv:
        pv = Preview(track_id=track.id, provider_id=provider.id)
        db.add(pv)
    if ext.provider == itunes.PROVIDER and provider.enabled and ext.preview_url:
        pv.preview_url = ext.preview_url
        pv.status = PreviewStatus.AVAILABLE
        pv.duration_seconds = itunes.PREVIEW_MAX_SECONDS
        pv.territories = [(ext.country or "").upper()]
        pv.rights_reference = itunes.RIGHTS_REFERENCE
        pv.expires_at = now() + PREVIEW_TTL
    elif ext.external_url:
        pv.preview_url, pv.status = None, PreviewStatus.EXTERNAL_ONLY
    else:
        pv.preview_url, pv.status = None, PreviewStatus.UNAVAILABLE
    pv.last_verified_at = now()


def find_duplicate(db: Session, track: Track, artist: Artist) -> Track | None:
    """Stesso titolo normalizzato, stesso artista normalizzato, durata entro 2 s."""
    rows = db.execute(
        select(Track, Artist).join(TrackArtist, TrackArtist.track_id == Track.id)
        .join(Artist, Artist.id == TrackArtist.artist_id)
        .where(Track.normalized_title == track.normalized_title, Track.id != track.id,
               Artist.sort_name == artist.sort_name, TrackArtist.role == "primary")
    ).all()
    for other, _ in rows:
        if track.duration_ms is None or other.duration_ms is None or abs(track.duration_ms - other.duration_ms) <= 2000:
            return other
    return None


def ingest_track(db: Session, ext: ExternalTrack) -> Track:
    provider = get_provider(db, ext.provider)
    link = db.scalar(select(ProviderTrack).where(ProviderTrack.provider_id == provider.id,
                                                 ProviderTrack.external_id == ext.external_id))
    if link:
        track = db.get(Track, link.track_id)
        link.external_url = ext.external_url or link.external_url
        link.last_verified_at = now()
        if ext.isrc and not track.isrc:
            track.isrc = ext.isrc
    else:
        track = db.scalar(select(Track).where(Track.isrc == ext.isrc)) if ext.isrc else None
        if not track:
            artist = _artist(db, provider, ext)
            album = _album(db, provider, ext, artist)
            track = Track(title=ext.title, normalized_title=normalize(ext.title), duration_ms=ext.duration_ms,
                          isrc=ext.isrc, explicit_status=ext.explicit, release_date=ext.release_date,
                          album_id=album.id if album else None, popularity_sources=[])
            db.add(track)
            db.flush()
            db.add(TrackArtist(track_id=track.id, artist_id=artist.id, role="primary"))
            db.flush()
            dup = find_duplicate(db, track, artist)
            if dup:
                a, b = sorted([dup.id, track.id], key=str)
                if not db.scalar(select(DuplicateCandidate).where(DuplicateCandidate.track_a_id == a,
                                                                  DuplicateCandidate.track_b_id == b)):
                    db.add(DuplicateCandidate(track_a_id=a, track_b_id=b, reason="titolo+artista+durata", score=0.8))
        db.add(ProviderTrack(track_id=track.id, provider_id=provider.id, external_id=ext.external_id,
                             external_url=ext.external_url, territory=(ext.country or "").upper() or None,
                             metadata_={"genre": ext.genre_name}, last_verified_at=now()))
    slug = genre_slug(ext.genre_name)
    tag = _tag(db, slug) if slug else None
    if tag and not db.get(TrackTag, (track.id, tag.id)):
        db.add(TrackTag(track_id=track.id, tag_id=tag.id, confidence=0.9, source=TagOrigin.provider))
    _preview(db, provider, track, ext)
    db.flush()
    return track


def apply_charts(db: Session, tracks_by_ext: dict[str, Track], charts: list[ChartEntry], home: str = "it",
                 configured: set[str] | None = None) -> None:
    """Segna come 'popular' le tracce presenti in almeno una classifica e azzera chi è uscito da tutte.
    Punteggio = posizione migliore; la classifica del paese dell'app pesa di più (1.0 contro 0.85).
    Ogni classifica resta in popularity_sources con paese, posizione e data."""
    ts = now()
    totals: dict[str, int] = {}
    for e in charts:
        totals[e.country] = max(totals.get(e.country, 0), e.rank)
    per_track: dict = {}
    for e in charts:
        t = tracks_by_ext.get(e.external_id)
        if t:
            per_track.setdefault(t.id, (t, []))[1].append(e)
    for t, entries in per_track.values():
        is_home = lambda e: e.country.lower() == home.lower()  # noqa: E731
        score = max((1.0 if is_home(e) else 0.85) * (1 - (e.rank - 1) / max(totals[e.country], 1) * 0.5) for e in entries)
        t.popularity_class = PopularityClass.popular
        t.popularity_score = round(score, 4)
        t.popularity_confidence = 0.9
        t.popularity_sources = [{"source": e.chart, "provider": e.provider, "country": e.country.upper(), "home": is_home(e),
                                 "rank": e.rank, "feed_updated": e.updated, "fetched_at": ts.isoformat()}
                                for e in sorted(entries, key=lambda e: (not is_home(e), e.rank))]
        t.popularity_updated_at = ts
    wanted = {c.upper() for c in (configured or {e.country for e in charts})}
    liked = set(db.scalars(select(Like.track_id)).all())
    for t in db.scalars(select(Track).where(Track.popularity_class == PopularityClass.popular)):
        if t.id not in per_track:
            old = {str(x.get("country", "")).upper() for x in (t.popularity_sources or []) if x.get("rank")}
            t.popularity_class = PopularityClass.unknown
            t.popularity_score = None
            t.popularity_confidence = None
            t.popularity_sources = [{"source": "apple_music_most_played", "note": "uscito dalle classifiche",
                                     "fetched_at": ts.isoformat()}]
            t.popularity_updated_at = ts
            # arrivato solo da classifiche che non usiamo più (es. Francia tolta): non lo riproponiamo
            # nemmeno come scoperta, a meno che qualcuno non lo abbia già messo tra i Mi piace
            if old and not (old & wanted) and t.id not in liked:
                t.hidden_reason = "chart_removed:" + ",".join(sorted(old))


def apply_chart(db: Session, tracks_by_ext: dict[str, Track], chart: list[ChartEntry]) -> None:
    """Compatibilità: una sola classifica, considerata quella di casa."""
    apply_charts(db, tracks_by_ext, chart, home=chart[0].country if chart else "it")
