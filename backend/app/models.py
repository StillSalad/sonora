"""Modello dati canonico (docs/DATABASE_SCHEMA.md).

Milestone 1 crea tutte le tabelle; le funzioni che le usano arrivano nelle milestone successive.
Nessuna tabella contiene file audio: le anteprime restano presso i provider autorizzati.
"""
import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (JSON, Boolean, Date, DateTime, Enum, Float, ForeignKey, Index, Integer,
                        String, Text, UniqueConstraint, Uuid, text)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base

JSONType = JSON().with_variant(JSONB(), "postgresql")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def pk() -> Mapped[uuid.UUID]:
    return mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


def created() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


def updated() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class PopularityClass(str, enum.Enum):
    popular = "popular"
    discovery = "discovery"
    unknown = "unknown"


class PreviewStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    EXTERNAL_ONLY = "EXTERNAL_ONLY"
    RIGHTS_PENDING = "RIGHTS_PENDING"
    BLOCKED = "BLOCKED"


class TagOrigin(str, enum.Enum):
    editorial = "editorial"
    provider = "provider"
    automatic = "automatic"
    user = "user"


class Visibility(str, enum.Enum):
    private = "private"
    public = "public"


class Role(str, enum.Enum):
    user = "user"
    admin = "admin"


# ---------- utenti e sessioni ----------
class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = pk()
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(64))
    avatar_url: Mapped[str | None] = mapped_column(String(1024))
    password_hash: Mapped[str | None] = mapped_column(String(255))
    auth_provider: Mapped[str] = mapped_column(String(32), default="password")
    role: Mapped[Role] = mapped_column(Enum(Role, native_enum=False, length=16), default=Role.user)
    is_private: Mapped[bool] = mapped_column(Boolean, default=True)
    age_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = created()
    updated_at: Mapped[datetime] = updated()
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UserSession(Base):
    """Sessione lato server: il cookie contiene solo un token opaco, qui ne salviamo l'hash."""
    __tablename__ = "user_sessions"
    id: Mapped[uuid.UUID] = pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = created()
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# ---------- catalogo ----------
class Artist(Base):
    __tablename__ = "artists"
    id: Mapped[uuid.UUID] = pk()
    canonical_name: Mapped[str] = mapped_column(String(512), index=True)
    sort_name: Mapped[str | None] = mapped_column(String(512))
    country_code: Mapped[str | None] = mapped_column(String(2))
    biography: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(1024))
    created_at: Mapped[datetime] = created()
    updated_at: Mapped[datetime] = updated()


class Album(Base):
    __tablename__ = "albums"
    id: Mapped[uuid.UUID] = pk()
    title: Mapped[str] = mapped_column(String(512))
    release_date: Mapped[date | None] = mapped_column(Date)
    album_type: Mapped[str | None] = mapped_column(String(32))
    artwork_url: Mapped[str | None] = mapped_column(String(1024))
    primary_artist_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("artists.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = created()
    updated_at: Mapped[datetime] = updated()


class Track(Base):
    __tablename__ = "tracks"
    __table_args__ = (
        Index("ix_tracks_isrc", "isrc", postgresql_where=text("isrc IS NOT NULL")),
        Index("ix_tracks_popularity", "popularity_class", "popularity_score"),
    )
    id: Mapped[uuid.UUID] = pk()
    title: Mapped[str] = mapped_column(String(512))
    normalized_title: Mapped[str] = mapped_column(String(512), index=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    isrc: Mapped[str | None] = mapped_column(String(12))
    explicit_status: Mapped[str | None] = mapped_column(String(16))
    release_date: Mapped[date | None] = mapped_column(Date)
    album_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("albums.id", ondelete="SET NULL"))
    popularity_score: Mapped[float | None] = mapped_column(Float)
    popularity_confidence: Mapped[float | None] = mapped_column(Float)
    popularity_class: Mapped[PopularityClass] = mapped_column(
        Enum(PopularityClass, native_enum=False, length=16), default=PopularityClass.unknown)
    popularity_sources: Mapped[list] = mapped_column(JSONType, default=list)
    popularity_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = created()
    updated_at: Mapped[datetime] = updated()


class TrackArtist(Base):
    __tablename__ = "track_artists"
    track_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tracks.id", ondelete="CASCADE"), primary_key=True)
    artist_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("artists.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[str] = mapped_column(String(16), primary_key=True, default="primary")


class Provider(Base):
    __tablename__ = "providers"
    id: Mapped[uuid.UUID] = pk()
    name: Mapped[str] = mapped_column(String(64), unique=True)
    provider_type: Mapped[str] = mapped_column(String(32))
    base_url: Mapped[str | None] = mapped_column(String(512))
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    terms_url: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = created()


class ProviderTrack(Base):
    __tablename__ = "provider_tracks"
    __table_args__ = (UniqueConstraint("provider_id", "external_id"),)
    id: Mapped[uuid.UUID] = pk()
    track_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tracks.id", ondelete="CASCADE"), index=True)
    provider_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("providers.id", ondelete="CASCADE"))
    external_id: Mapped[str] = mapped_column(String(255))
    external_url: Mapped[str | None] = mapped_column(String(1024))
    territory: Mapped[str | None] = mapped_column(String(8))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONType, default=dict)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Preview(Base):
    __tablename__ = "previews"
    id: Mapped[uuid.UUID] = pk()
    track_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tracks.id", ondelete="CASCADE"), index=True)
    provider_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("providers.id", ondelete="CASCADE"))
    preview_url: Mapped[str | None] = mapped_column(String(1024))
    status: Mapped[PreviewStatus] = mapped_column(
        Enum(PreviewStatus, native_enum=False, length=16), default=PreviewStatus.RIGHTS_PENDING)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    territories: Mapped[list] = mapped_column(JSONType, default=list)
    rights_reference: Mapped[str | None] = mapped_column(String(512))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# ---------- tag ----------
class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("category", "slug"),)
    id: Mapped[uuid.UUID] = pk()
    slug: Mapped[str] = mapped_column(String(64))
    label: Mapped[str] = mapped_column(String(128))
    category: Mapped[str] = mapped_column(String(32))
    language: Mapped[str] = mapped_column(String(8), default="it")
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="active")
    origin: Mapped[TagOrigin] = mapped_column(Enum(TagOrigin, native_enum=False, length=16), default=TagOrigin.editorial)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = created()


class TrackTag(Base):
    __tablename__ = "track_tags"
    __table_args__ = (Index("ix_track_tags_tag", "tag_id", "track_id"),)
    track_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tracks.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    source: Mapped[TagOrigin] = mapped_column(Enum(TagOrigin, native_enum=False, length=16))
    verified_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = created()


class TagRelation(Base):
    __tablename__ = "tag_relations"
    source_tag_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    target_tag_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    relation_type: Mapped[str] = mapped_column(String(32), primary_key=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0)


# ---------- raccolte e attività ----------
class Collection(Base):
    __tablename__ = "collections"
    __table_args__ = (Index("ix_collections_owner", "owner_user_id", "visibility"),)
    id: Mapped[uuid.UUID] = pk()
    owner_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text)
    cover_url: Mapped[str | None] = mapped_column(String(1024))
    visibility: Mapped[Visibility] = mapped_column(Enum(Visibility, native_enum=False, length=16), default=Visibility.private)
    is_dynamic: Mapped[bool] = mapped_column(Boolean, default=False)
    rules: Mapped[dict] = mapped_column(JSONType, default=dict)
    created_at: Mapped[datetime] = created()
    updated_at: Mapped[datetime] = updated()


class CollectionTrack(Base):
    __tablename__ = "collection_tracks"
    collection_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True)
    track_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tracks.id", ondelete="CASCADE"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    added_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = created()


class Like(Base):
    __tablename__ = "likes"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    track_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tracks.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = created()


class Follow(Base):
    __tablename__ = "follows"
    follower_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    target_type: Mapped[str] = mapped_column(String(16), primary_key=True)
    target_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    created_at: Mapped[datetime] = created()


class ListeningEvent(Base):
    __tablename__ = "listening_events"
    __table_args__ = (Index("ix_events_user_time", "user_id", "created_at"),)
    id: Mapped[uuid.UUID] = pk()
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    track_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tracks.id", ondelete="CASCADE"))
    event_type: Mapped[str] = mapped_column(String(32))
    listened_ms: Mapped[int | None] = mapped_column(Integer)
    session_id: Mapped[str | None] = mapped_column(String(64))
    source_surface: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = created()


class UserPreference(Base):
    __tablename__ = "user_preferences"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    preference_type: Mapped[str] = mapped_column(String(32), primary_key=True)
    preference_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    source: Mapped[str] = mapped_column(String(32), default="explicit")
    updated_at: Mapped[datetime] = updated()


class ConnectedAccount(Base):
    __tablename__ = "connected_accounts"
    id: Mapped[uuid.UUID] = pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("providers.id", ondelete="CASCADE"))
    provider_user_id: Mapped[str | None] = mapped_column(String(255))
    encrypted_token_reference: Mapped[str | None] = mapped_column(String(512))
    scopes: Mapped[list] = mapped_column(JSONType, default=list)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    connected_at: Mapped[datetime] = created()
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Report(Base):
    __tablename__ = "reports"
    id: Mapped[uuid.UUID] = pk()
    reporter_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    target_type: Mapped[str] = mapped_column(String(16))
    target_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="open")
    moderator_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = created()
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[uuid.UUID] = pk()
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(64))
    target_type: Mapped[str | None] = mapped_column(String(32))
    target_id: Mapped[str | None] = mapped_column(String(64))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONType, default=dict)
    created_at: Mapped[datetime] = created()


# ---------- aggiunte Milestone 2–3 ----------
class ProviderArtist(Base):
    __tablename__ = "provider_artists"
    __table_args__ = (UniqueConstraint("provider_id", "external_id"),)
    id: Mapped[uuid.UUID] = pk()
    artist_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("artists.id", ondelete="CASCADE"), index=True)
    provider_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("providers.id", ondelete="CASCADE"))
    external_id: Mapped[str] = mapped_column(String(255))
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProviderAlbum(Base):
    __tablename__ = "provider_albums"
    __table_args__ = (UniqueConstraint("provider_id", "external_id"),)
    id: Mapped[uuid.UUID] = pk()
    album_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("albums.id", ondelete="CASCADE"), index=True)
    provider_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("providers.id", ondelete="CASCADE"))
    external_id: Mapped[str] = mapped_column(String(255))
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DuplicateCandidate(Base):
    """Due tracce che potrebbero essere la stessa registrazione. Mai fuse in automatico:
    restano entrambe finché un amministratore non decide (Milestone 8)."""
    __tablename__ = "duplicate_candidates"
    __table_args__ = (UniqueConstraint("track_a_id", "track_b_id"),)
    id: Mapped[uuid.UUID] = pk()
    track_a_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tracks.id", ondelete="CASCADE"))
    track_b_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tracks.id", ondelete="CASCADE"))
    reason: Mapped[str] = mapped_column(String(128))
    score: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(16), default="open")
    created_at: Mapped[datetime] = created()


class FeedImpression(Base):
    """Brani già mostrati in una sessione di feed: niente ripetizioni e finestra 80/20 verificabile."""
    __tablename__ = "feed_impressions"
    __table_args__ = (UniqueConstraint("session_id", "track_id"), Index("ix_impressions_session_pos", "session_id", "position"))
    id: Mapped[uuid.UUID] = pk()
    session_id: Mapped[str] = mapped_column(String(64))
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    track_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tracks.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer)
    slot: Mapped[str] = mapped_column(String(16))  # popular | discovery
    created_at: Mapped[datetime] = created()
