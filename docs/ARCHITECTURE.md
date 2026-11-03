# SONORA — Architettura (Milestone 0)

## Decisioni
| Area | Scelta | Perché |
|---|---|---|
| Frontend | React 18 + TypeScript + Vite + Tailwind 3 | Richiesto dal master prompt; build veloce, tipi stretti |
| PWA | vite-plugin-pwa (Workbox) | Manifest, service worker, installazione; precache solo della shell (~440 KB) |
| Backend | FastAPI + SQLAlchemy 2 + Alembic | Richiesto; OpenAPI automatico su `/api/v1/docs` |
| Database | PostgreSQL 16 in produzione, SQLite per sviluppo rapido e test | Stessi modelli: JSONB su Postgres, JSON su SQLite |
| Sessioni | Cookie httpOnly con token opaco, hash salvato in `user_sessions` | Logout e revoca reali lato server; niente token nel JavaScript |
| Password | Argon2id | Standard attuale |
| CSRF | SameSite=Lax + controllo Origin + header `X-Sonora-Client` | Un sito terzo non può inviare l'header senza preflight CORS |
| Rate limit | In memoria per processo su login/registrazione | Da spostare su Redis quando ci saranno più istanze (M3) |
| Errori | `{code, message, request_id}` ovunque | Come da API_SPEC |
| Funzioni non pronte | `/api/v1/meta` dichiara cosa è attivo; il frontend lo legge | Nessuna funzione finta presentata come funzionante |

## Struttura
```
backend/   app/ (config, db, models, security, middleware, errors, routers/)  alembic/  tests/
frontend/  src/ (pages/, components/, context/, lib/, assets/)  public/ (favicon, icone PWA)
docs/      architettura, API, schema DB, regole legali, roadmap
```

## Mappa schermate
| Percorso | Schermata | Stato in M1 |
|---|---|---|
| `/` | Per te (feed verticale) | Attivo (M3) |
| `/esplora` | Mood + 27 generi | Attiva (navigazione), contenuti da M2/M4 |
| `/esplora/genere/:slug`, `/esplora/mood/:slug` | Pagina tag | Generi attivi (tag provider), mood in M4 |
| `/cerca` | Ricerca | Attiva (M2) |
| `/artista/:id` | Artista | Attiva (M2) |
| `/raccolte` | Raccolte e preferiti | Mi piace attivo; raccolte in M5 |
| `/profilo` | Profilo, Music DNA, impostazioni | Account, tema, installazione, logout, eliminazione attivi |
| `/accedi`, `/registrati`, `/privacy` | Account | Attivi |
| Admin | Dashboard | M8 |

## Design tokens
Colori in `frontend/src/index.css` come variabili RGB (tema scuro predefinito + chiaro con contrasto AA):
bg #0B0D14, surface #151925, surface2 #202638, primary #8B5CF6, secondary #38BDF8, accent #E879F9, ink #F5F6FA, muted #969DB0.
Tipografia: Bricolage Grotesque (titoli), Figtree (testo), incluse nel bundle per funzionare offline.
Asset: un file per elemento in `frontend/src/assets`, manifest in `docs/asset_manifest.json`.

## Fattibilità provider (da verificare sui termini aggiornati prima di ogni integrazione)
| Provider | Uso previsto | Serve | Rischio / nota |
|---|---|---|---|
| MusicBrainz | Metadati, ISRC, deduplicazione (M2) | User-Agent identificativo, max 1 richiesta/s | Basso; dati CC0, copertine via Cover Art Archive con licenze proprie |
| Apple Music API / MusicKit | Catalogo, copertine, anteprime, link (M2–M3) | Apple Developer Program, chiave MusicKit (JWT) | Medio: anteprime solo secondo i termini Apple; attribuzione obbligatoria |
| Classifiche Apple (RSS marketing) | Segnale di popolarità per l'80/20 | Nessuna chiave | Da confermare uso consentito; fonte e data salvate in `popularity_sources` |
| Spotify Web API | Link esterni, eventuale salvataggio in playlist dell'utente (M7) | App approvata, OAuth | Alto: `preview_url` deprecato, restrizioni sui nuovi usi; non base del prodotto |
| YouTube Music | Solo link esterni | — | Nessuna API pubblica ufficiale per le playlist di YouTube Music |
| Lyra | Adapter configurabile | Schema fornito dal proprietario | Non implementabile senza documentazione |

## Registro rischi
| Rischio | Impatto | Mitigazione |
|---|---|---|
| Diritti delle anteprime incerti | Alto | Stato `RIGHTS_PENDING` di default; l'audio parte solo con stato `AVAILABLE` verificato |
| Popolarità non attendibile per l'80/20 | Medio | Classe `unknown` quando i segnali mancano; tolleranza dichiarata nel mixer |
| Fusioni errate tra provider | Medio | Merge automatico solo su ISRC; il resto va in revisione admin |
| Limiti di frequenza dei provider | Medio | Cache dei metadati, code, rispetto dei limiti (MusicBrainz 1 req/s) |
| Utenti minorenni nella community | Alto | Età minima 14 confermata, profili privati di default, segnalazioni e blocchi (M6) |
| Rate limit in memoria con più istanze | Basso ora | Redis in M3 |
| Hosting a pagamento | Medio | Tutto configurabile via variabili d'ambiente, nessun provider fissato |
