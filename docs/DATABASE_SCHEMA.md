# DATABASE SCHEMA — SONORA (proposta iniziale)

## Principi
- UUID come primary key.
- Timestamp UTC.
- Provider IDs separati dai canonical IDs.
- Provenienza dei metadati tracciata.
- N:M per tag, artisti, raccolte e tracce.
- Nessuna tabella audio file: le anteprime restano presso provider autorizzati.

## Entità principali

### users
id, email, username, display_name, avatar_url, password_hash/auth_provider,
is_private, created_at, updated_at, deleted_at

### artists
id, canonical_name, sort_name, country_code, biography, image_url,
created_at, updated_at

### albums
id, title, release_date, album_type, artwork_url, primary_artist_id,
created_at, updated_at

### tracks
id, title, normalized_title, duration_ms, isrc, explicit_status,
release_date, album_id, popularity_score, popularity_confidence,
popularity_class (popular/discovery/unknown), popularity_sources JSONB,
popularity_updated_at, created_at, updated_at

### track_artists
track_id, artist_id, role (primary/featured/composer/remixer)

### providers
id, name, provider_type, base_url, enabled, terms_url, created_at

### provider_tracks
id, track_id, provider_id, external_id, external_url, territory,
metadata JSONB, last_verified_at, UNIQUE(provider_id, external_id)

### previews
id, track_id, provider_id, preview_url, status, duration_seconds,
territories JSONB, rights_reference, expires_at, last_verified_at

### tags
id, slug, label, category, language, description, status,
origin (editorial/provider/automatic/user), confidence, created_at

### track_tags
track_id, tag_id, confidence, source, verified_by, created_at,
UNIQUE(track_id, tag_id)

### tag_relations
source_tag_id, target_tag_id, relation_type, weight

### collections
id, owner_user_id, title, description, cover_url, visibility,
is_dynamic, rules JSONB, created_at, updated_at

### collection_tracks
collection_id, track_id, position, added_by, created_at

### likes
user_id, track_id, created_at, UNIQUE(user_id, track_id)

### follows
follower_user_id, target_type, target_id, created_at

### listening_events
id, user_id, track_id, event_type, listened_ms, session_id,
source_surface, created_at

Event types: preview_start, preview_progress, preview_complete, skip,
like, unlike, save, unsave, external_open, search_click.

### user_preferences
user_id, preference_type, preference_key, weight, source, updated_at

### connected_accounts
id, user_id, provider_id, provider_user_id, encrypted_token_reference,
scopes JSONB, status, connected_at, expires_at

### reports
id, reporter_user_id, target_type, target_id, reason, status,
moderator_user_id, created_at, resolved_at

### audit_logs
id, actor_user_id, action, target_type, target_id, metadata JSONB, created_at

## Indici raccomandati
- tracks(isrc) WHERE isrc IS NOT NULL
- tracks(normalized_title)
- tracks(popularity_class, popularity_score DESC)
- provider_tracks(provider_id, external_id)
- tags(category, slug)
- track_tags(tag_id, track_id)
- listening_events(user_id, created_at DESC)
- collections(owner_user_id, visibility)
- full-text index su tracks.title e artists.canonical_name

## Nota
Questo è un modello concettuale iniziale. Le migrazioni SQLAlchemy/Alembic devono essere
generate e testate durante la milestone Foundation.
