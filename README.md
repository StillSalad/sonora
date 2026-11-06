# SONORA

PWA per scoprire musica: un feed verticale con 8 brani famosi e 2 da scoprire ogni 10, generi e mood da esplorare, raccolte e il tuo Music DNA.
SONORA non è un servizio di streaming: mostrerà copertine, anteprime e link solo dove i provider lo consentono.

**Stato: 0.5.0.** Funzionano:
- scelta iniziale di generi e artisti, feed che segue i tuoi gusti e lo spiega;
- gesti sulla copertina (tocco, doppio tocco, tieni premuto), "Non fa per me" con Annulla;
- "Altri brani così", mood votati dalla community, scoperta del giorno, condivisione come storia;
- feed Per te con brani veri da Apple Music, regola 80/20 e spiegazione di ogni proposta;
- anteprime di 30 secondi solo dove il diritto è verificato, con link "Ascolta su Apple Music";
- ricerca (catalogo locale + Apple quando mancano risultati), pagine dei 27 generi, pagine artista;
- Mi piace e lista dei preferiti, account, tema chiaro/scuro, installazione come app.

Non ancora attivi (e dichiarati tali nell'app): mood, raccolte, Music DNA, community, collegamento account Spotify/Apple, admin.

---

## Avvio passo passo (principianti)

Ti servono: **Python 3.11+** e **Node.js 20+**. Docker è facoltativo.
Apri due finestre del terminale: una per il backend, una per il frontend.

### 1. Backend (finestra 1)
```bash
cd backend
python -m venv .venv
# Windows:  .venv\Scripts\activate      macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env                # su Windows: copy ..\.env.example .env
alembic upgrade head                   # crea le tabelle (SQLite di default: sonora_dev.db)
uvicorn app.main:app --reload --port 8000
```
Verifica: apri http://localhost:8000/api/v1/health → deve dire `"status": "ok"`.
Documentazione API interattiva: http://localhost:8000/api/v1/docs

### 2. Frontend (finestra 2)
```bash
cd frontend
npm install
npm run dev
```
Apri http://localhost:5173. Il frontend inoltra da solo le chiamate `/api` al backend.

### 3. Riempi il catalogo con musica vera (finestra 1, backend fermo o in un terzo terminale)
```bash
cd backend
python -m app.jobs.ingest
```
Scarica la classifica Apple Music italiana (100 brani) e circa 40 brani per ognuno dei 27 generi.
Ci mette 5–6 minuti perché Apple permette circa 20 richieste al minuto: è normale, lascialo finire.
Per una prova veloce: `python -m app.jobs.ingest --solo-classifica` (meno di un minuto).
Ripetilo una volta al giorno per aggiornare classifiche e anteprime (le anteprime scadono dopo 7 giorni).

Senza internet? `python -m app.jobs.seed_demo` crea 60 brani **[DEMO]** fittizi, senza audio né copertine.
Si vedono solo con `DEMO_MODE=true` nel file `.env`.

### 4. Prova
1. Apri **Per te**: tocca play sul primo brano. Dal secondo in poi, scorrendo, l'anteprima parte da sola.
2. Ogni 5 brani uno è una scoperta (etichetta fucsia), gli altri sono in classifica (etichetta azzurra).
3. Cerca un artista che non è nel catalogo: SONORA lo chiede ad Apple e lo aggiunge.
4. Crea un account, metti Mi piace a qualche brano: lo ritrovi in Raccolte, e il feed inizia a spiegarti "Perché ti piace il genere…".
5. Spegni il backend: compare l'avviso "Il server di SONORA non risponde" con il pulsante Riprova.

### Usare PostgreSQL invece di SQLite
```bash
docker compose up -d db
```
Poi in `backend/.env` metti `DATABASE_URL=postgresql+psycopg://sonora:sonora@localhost:5432/sonora` e rilancia `alembic upgrade head`.

## Test
```bash
cd backend && python -m pytest          # 64 test: account e sicurezza, provider, import, deduplicazione, mixer 80/20, feed, anteprime, ricerca
cd frontend && npm test                 # 25 test: scelta iniziale, gesti, menu, feed e player, ricerca, mood, account
cd frontend && npm run typecheck
```

## Build
- `npm run build` nel frontend → cartella `frontend/dist`, installabile come PWA (service worker incluso).
- `npm run build:preview` → un unico file HTML per mostrare la grafica senza server (niente account).

## Pubblicarla online e usarla sul telefono
Guida passo passo in **`docs/DEPLOY.md`**: Netlify (app) + Render (server) + Supabase (database), tutto gratuito.
I file di configurazione sono già pronti: `netlify.toml`, `render.yaml`, `docs/github-workflow-sonora.yml` (estrazione dello zip + aggiornamento giornaliero).

## Documenti
- `docs/ARCHITECTURE.md` — decisioni, mappa schermate, matrice provider, registro rischi
- `docs/API_SPEC.md`, `docs/DATABASE_SCHEMA.md`, `docs/LEGAL_AND_PROVIDER_RULES.md`, `docs/ROADMAP.md`
- `docs/DEPLOY.md` — pubblicazione online passo passo
- `docs/PROVIDERS.md` — Apple, classifiche, MusicBrainz: cosa usiamo e a quali condizioni
- `docs/PRIVACY_RETENTION.md` — dati conservati e cancellazione
- `docs/asset_manifest.json` — tutti gli asset grafici
- `CHANGELOG.md`
