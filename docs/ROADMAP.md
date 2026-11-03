# IMPLEMENTATION ROADMAP

## Milestone 0 — Discovery and setup
Deliver: architecture decisions, provider feasibility matrix, repo, environment template,
risk register, screen map, design tokens.
Acceptance: no invented API capabilities; provider risks documented.

## Milestone 1 — Foundation
Deliver: React/Vite/TypeScript app, FastAPI backend, PostgreSQL, migrations, auth scaffold,
responsive shell, navigation, design system, PWA manifest/service worker.
Acceptance: installable build, working routes, lint/typecheck/tests.

## Milestone 2 — Catalog and search
Deliver: canonical track/artist/album models, provider adapter interface, MusicBrainz
metadata adapter (respect rate limits), seeded demo records, deduplication review,
search and filters.
Acceptance: provider origin is visible; duplicate candidates are not silently merged.

## Milestone 3 — Feed and preview
Deliver: vertical feed, player state machine, preview-rights state, external links,
event logging, 80/20 rolling-window mixer.
Acceptance: no unlicensed audio; no repeated track in a session; fallback for no preview.

## Milestone 4 — Tags and Explore
Deliver: multi-tag taxonomy, tag relations, category pages, mood pages, combined filters.
Acceptance: tag origin/confidence visible to admin; tag filters tested.

## Milestone 5 — Collections and profile
Deliver: visual boards, private/public collections, likes, saves, profile, Music DNA.
Acceptance: ownership and privacy enforced server-side.

## Milestone 6 — Recommendation and community
Deliver: explainable recommendations, discovery quota, diversity controls, follows,
public collections, reports, block/mute.
Acceptance: user controls affect future feed; skip is not treated as dislike by default.

## Milestone 7 — Integrations
Deliver: OAuth adapter framework, external links, only verified supported playlist actions.
Acceptance: no credentials stored in plaintext; unsupported capability is shown honestly.

## Milestone 8 — Admin and production
Deliver: catalog moderation, preview-rights admin, audit logs, monitoring, backups,
accessibility pass, security review, deployment guide.
Acceptance: test suite green; privacy/deletion process tested; provider compliance reviewed.
