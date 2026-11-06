"""Gusti espliciti (scelti all'inizio) e segnali negativi ('Non fa per me')."""
import re
import uuid
from collections import Counter
from dataclasses import dataclass, field

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..catalog.genres import GENRE_LABELS
from ..models import Artist, FeedFeedback, User, UserPreference

DEVICE_RE = re.compile(r"^[A-Za-z0-9-]{16,64}$")
MAX_GENRES, MAX_ARTISTS = 12, 40


@dataclass
class Prefs:
    genres: set[str] = field(default_factory=set)
    artists: set[uuid.UUID] = field(default_factory=set)
    artist_names: dict = field(default_factory=dict)

    @property
    def empty(self) -> bool:
        return not self.genres and not self.artists


@dataclass
class Negatives:
    tracks: set = field(default_factory=set)
    artists: set = field(default_factory=set)
    genres: Counter = field(default_factory=Counter)


def valid_device(v: str | None) -> str | None:
    return v if v and DEVICE_RE.match(v) else None


def parse_prefs(genres: str | None, artists: str | None) -> Prefs:
    p = Prefs()
    for g in (genres or "").split(",")[:MAX_GENRES]:
        if g in GENRE_LABELS:
            p.genres.add(g)
    for a in (artists or "").split(",")[:MAX_ARTISTS]:
        try:
            p.artists.add(uuid.UUID(a))
        except ValueError:
            continue
    return p


def stored_prefs(db: Session, user: User) -> Prefs:
    p = Prefs()
    for t, k in db.execute(select(UserPreference.preference_type, UserPreference.preference_key)
                           .where(UserPreference.user_id == user.id, UserPreference.source == "explicit")).all():
        if t == "genre" and k in GENRE_LABELS:
            p.genres.add(k)
        elif t == "artist":
            try:
                p.artists.add(uuid.UUID(k))
            except ValueError:
                pass
    return p


def resolve_prefs(db: Session, user: User | None, sent: Prefs) -> Prefs:
    """Le preferenze inviate dall'app (salvate sul dispositivo) valgono per tutti; con un account e
    nessuna preferenza inviata si usano quelle salvate sul server."""
    p = sent if not sent.empty or not user else stored_prefs(db, user)
    if p.artists:
        p.artist_names = dict(db.execute(select(Artist.id, Artist.canonical_name).where(Artist.id.in_(p.artists))).all())
    return p


def negatives(db: Session, user: User | None, device: str | None) -> Negatives:
    who = []
    if user:
        who.append(FeedFeedback.user_id == user.id)
    if device:
        who.append(FeedFeedback.device_id == device)
    n = Negatives()
    if not who:
        return n
    for f in db.scalars(select(FeedFeedback).where(or_(*who))).all():
        if f.kind == "not_interested" and f.track_id:
            n.tracks.add(f.track_id)
        elif f.kind == "hide_artist" and f.artist_id:
            n.artists.add(f.artist_id)
        elif f.kind == "less_genre" and f.genre_slug:
            n.genres[f.genre_slug] += 1
    return n
