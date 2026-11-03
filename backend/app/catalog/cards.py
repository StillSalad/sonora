"""Scheda pubblica di una traccia. L'URL dell'anteprima compare SOLO se il diritto è verificato,
non scaduto, valido per il territorio e il provider è attivo (API_SPEC: Feed)."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (Album, Artist, Like, Preview, PreviewStatus, Provider, ProviderTrack, Tag, Track, TrackArtist,
                      TrackTag, User)

PROVIDER_LINK = {"itunes": ("apple_music", "Apple Music")}


def _aware(dt):
    return dt if dt is None or dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def preview_view(pv: Preview | None, provider: Provider | None, country: str) -> dict:
    if not pv:
        return {"status": "UNAVAILABLE", "url": None, "duration_seconds": None, "provider": None}
    status = pv.status.value
    allowed = (pv.status == PreviewStatus.AVAILABLE and pv.preview_url and provider and provider.enabled)
    if allowed and pv.expires_at and _aware(pv.expires_at) < datetime.now(timezone.utc):
        allowed, status = False, "RIGHTS_PENDING"  # scaduta: va riverificata prima di suonare
    if allowed and pv.territories and country.upper() not in pv.territories:
        allowed, status = False, "UNAVAILABLE"
    return {"status": status, "url": pv.preview_url if allowed else None,
            "duration_seconds": pv.duration_seconds if allowed else None,
            "provider": provider.name if provider else None}


def track_card(db: Session, track: Track, user: User | None, country: str) -> dict:
    artists = db.execute(select(Artist, TrackArtist.role).join(TrackArtist, TrackArtist.artist_id == Artist.id)
                         .where(TrackArtist.track_id == track.id)).all()
    album = db.get(Album, track.album_id) if track.album_id else None
    tags = db.scalars(select(Tag).join(TrackTag, TrackTag.tag_id == Tag.id).where(TrackTag.track_id == track.id)).all()
    links_rows = db.execute(select(ProviderTrack, Provider).join(Provider, Provider.id == ProviderTrack.provider_id)
                            .where(ProviderTrack.track_id == track.id)).all()
    pv_rows = db.execute(select(Preview, Provider).join(Provider, Provider.id == Preview.provider_id)
                         .where(Preview.track_id == track.id)).all()
    playable = [preview_view(pv, pr, country) for pv, pr in pv_rows]
    preview = next((p for p in playable if p["url"]), playable[0] if playable else preview_view(None, None, country))

    links, artwork = [], None
    for pt, pr in links_rows:
        if pr.name in PROVIDER_LINK and pt.external_url:
            key, label = PROVIDER_LINK[pr.name]
            links.append({"provider": key, "label": f"Ascolta su {label}", "url": pt.external_url})
            if album and album.artwork_url and not artwork:
                artwork = {"url": album.artwork_url, "attribution": label}
    is_demo = any(pr.name == "demo" for _, pr in links_rows)
    liked = bool(user and db.get(Like, (user.id, track.id)))
    return {
        "id": str(track.id), "title": track.title,
        "artists": [{"id": str(a.id), "name": a.canonical_name, "role": role} for a, role in artists],
        "album": {"id": str(album.id), "title": album.title} if album else None,
        "release_year": track.release_date.year if track.release_date else None,
        "duration_ms": track.duration_ms, "explicit": track.explicit_status == "explicit",
        "artwork": artwork,
        "tags": [{"slug": t.slug, "label": t.label, "category": t.category, "origin": t.origin.value} for t in tags],
        "popularity": {"class": track.popularity_class.value, "score": track.popularity_score,
                       "confidence": track.popularity_confidence, "sources": track.popularity_sources or [],
                       "updated_at": track.popularity_updated_at.isoformat() if track.popularity_updated_at else None},
        "preview": preview, "links": links, "liked": liked, "demo": is_demo,
        "providers": [{"name": pr.name, "external_id": pt.external_id,
                       "last_verified_at": pt.last_verified_at.isoformat() if pt.last_verified_at else None}
                      for pt, pr in links_rows],
    }
