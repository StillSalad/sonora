# Changelog

## 0.3.1 — Pubblicazione online (2026-11-02)
### Aggiunto
- Configurazioni pronte: `render.yaml` (server), `netlify.toml` + `scripts/netlify-files.mjs` (app con proxy `/api` sullo stesso dominio), workflow GitHub per l'aggiornamento giornaliero.
- `POST /api/v1/internal/ingest` protetto da token; import automatico al primo avvio se il catalogo è vuoto.
- `DATABASE_URL` accetta le stringhe `postgres://`/`postgresql://` di Supabase e Render; in produzione SQLite viene rifiutato.
- Rate limit sull'IP reale del visitatore dietro proxy (`TRUST_PROXY`).
- L'app aspetta il risveglio del server gratuito ("SONORA si sta avviando") invece di dare errore.
- Guida `docs/DEPLOY.md`.

### Verificato
- Migrazioni e tutti i 44 test backend eseguiti anche su PostgreSQL 16.
- Prova completa in modalità produzione: cookie httpOnly + Secure + SameSite=Lax, sessione persistente, preferiti su PostgreSQL.

## 0.3.0 — Milestone 2 + 3 (2026-11-02)
### Aggiunto
- Interfaccia comune dei provider; adapter iTunes Search API + classifiche Apple Marketing Tools (con ripiego tra i due host), adapter MusicBrainz per ISRC (solo match univoci), limiti di frequenza rispettati.
- Catalogo canonico: artisti, album e tracce con collegamenti per provider e data di verifica; fusione automatica solo per ISRC identico; corrispondenze incerte salvate in `duplicate_candidates`, mai fuse.
- Job `python -m app.jobs.ingest` (classifica + 27 generi) e `python -m app.jobs.seed_demo` (dati fittizi marcati [DEMO]).
- Anteprime con stato (AVAILABLE, EXTERNAL_ONLY, RIGHTS_PENDING, UNAVAILABLE, BLOCKED), territorio, durata, riferimento ai termini e scadenza: l'URL esce dall'API solo se tutto è valido.
- Mixer 80/20 a finestra mobile di 50 (40 + 10), nessuna ripetizione per sessione, diversità di artista e genere, tolleranza dichiarata, spiegazioni semplici.
- API: `/feed`, `/feed/events`, `/search` (locale + Apple con cache), `/tracks/{id}`, `/tracks/{id}/availability`, `/artists/{id}`, `/albums/{id}`, `/tags`, `/tags/{slug}/tracks`, Mi piace e `/me/likes`.
- Frontend: feed verticale a schede, player con macchina a stati (stop a 30 s, audio solo dopo il primo gesto, pausa quando l'app va in background), muto, condivisione, ricerca, pagine genere e artista, preferiti in Raccolte.
- Libreria asset: 6 icone del player (play, pausa, cuore, cuore pieno, volume, muto).
- Migrazione 0002 con provider e tag di base. Test: 41 backend, 15 frontend.

### Corretto
- Il mixer allentava il vincolo sull'artista prima di quello sul genere.
- Il feed poteva aprirsi sull'ultima sezione invece che sul primo brano.

### Prossimo: Milestone 4 — tag engine ed Esplora
Tassonomia multi-tag con relazioni, mood con fonte e confidenza, filtri combinati (es. Pop + Nostalgico + 2010s).

## 0.1.0 — Milestone 0 + 1 (2026-11-02)
### Aggiunto
- Architettura, matrice provider, registro rischi, mappa schermate (`docs/ARCHITECTURE.md`).
- Backend FastAPI: modello dati completo (21 tabelle), migrazione Alembic iniziale, `/health`, `/meta` con lo stato reale delle funzioni.
- Account: registrazione con conferma età minima, accesso, sessioni revocabili lato server, logout, `/auth/me`, `/auth/session`, eliminazione account con anonimizzazione.
- Sicurezza: Argon2id, cookie httpOnly SameSite=Lax, protezione CSRF (Origin + header), rate limit su login e registrazione, header di sicurezza, envelope di errore uniforme.
- Frontend React/TS/Vite/Tailwind: navigazione (barra in basso su mobile, laterale su desktop), Per te, Esplora con 12 mood e 27 generi, pagine genere/mood, Cerca, Raccolte, Profilo, Accedi, Crea account, Privacy, 404.
- Tema scuro predefinito e chiaro, avviso offline/server non raggiungibile con riprova, installazione PWA (prompt nativo o istruzioni iOS), service worker con precache della sola shell.
- Libreria asset: 72 file separati (aggiunte 10 icone di interfaccia).
- Test: 13 backend (pytest), 8 frontend (Vitest + Testing Library).

### Prossimo: Milestone 2 — catalogo e ricerca
Adapter provider con interfaccia comune, adapter MusicBrainz (metadati, 1 richiesta/s), modello canonico con provenienza visibile, dati demo marcati come fittizi, candidati duplicati in revisione, ricerca e filtri.
