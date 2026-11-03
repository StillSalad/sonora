"""Dati di base (gli stessi della migrazione 0002), usati da test e strumenti locali."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Provider, Tag, TagOrigin
from .genres import GENRE_LABELS, MOOD_LABELS

PROVIDERS = [
    ("itunes", "catalog_preview", "https://itunes.apple.com", True, "https://performance-partners.apple.com/search-api"),
    ("musicbrainz", "metadata", "https://musicbrainz.org/ws/2", False, "https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting"),
    ("demo", "demo", None, True, None),
]


def ensure_base_data(db: Session) -> None:
    for name, kind, url, enabled, terms in PROVIDERS:
        if not db.scalar(select(Provider).where(Provider.name == name)):
            db.add(Provider(name=name, provider_type=kind, base_url=url, enabled=enabled, terms_url=terms))
    for cat, labels in (("genre", GENRE_LABELS), ("mood", MOOD_LABELS)):
        for slug, label in labels.items():
            if not db.scalar(select(Tag).where(Tag.category == cat, Tag.slug == slug)):
                db.add(Tag(slug=slug, label=label, category=cat, origin=TagOrigin.editorial))
    db.commit()
