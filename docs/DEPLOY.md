# Pubblicare SONORA online (gratis) e installarla sul telefono

Schema: **Netlify** (l'app che apri) → inoltra `/api` a → **Render** (il server Python) → salva su → **Supabase** (il database).
Per il telefono è tutto un solo indirizzo `https://…netlify.app`, quindi l'accesso funziona anche su iPhone.

Tempo: circa 30 minuti la prima volta. Costo: 0 €.

---

## 1. Metti il progetto su GitHub (si può fare dal telefono)
1. github.com → **+** → *New repository* → nome `sonora`, **Private**, senza README → *Create repository*.
2. *creating a new file* (o *Add file → Create new file*): come nome scrivi `.github/workflows/sonora.yml`
   e incolla il contenuto di `docs/github-workflow-sonora.yml` → *Commit changes*.
3. *Add file → Upload files* → scegli `sonora_github.zip` → *Commit changes*.
4. Dopo circa un minuto l'automazione (scheda *Actions*) estrae lo zip e lo cancella: nella pagina del repository
   compaiono `backend`, `frontend`, `docs`, `render.yaml`, `netlify.toml`.

Per aggiornare il progetto in futuro: carica di nuovo uno zip con la stessa struttura, verrà estratto sopra.

## 2. Crea il database su Supabase
1. supabase.com → *New project* → nome `sonora`, regione **Frankfurt** (vicina all'Italia), scegli una password del database e salvala.
2. Quando il progetto è pronto: pulsante **Connect** in alto → scheda *Connection string* → **Session pooler**.
   Usa proprio *Session pooler* (porta 5432): la connessione "Direct" non funziona da Render e il "Transaction pooler" (porta 6543) non è compatibile.
3. Copia la stringa e sostituisci `[YOUR-PASSWORD]` con la tua password.
   Se la password contiene simboli come `@ # / ?`, cambiala con una di sole lettere e numeri: quei simboli rompono l'indirizzo.

Le tabelle le crea il server da solo al primo avvio: su Supabase non devi fare altro.

## 3. Pubblica il server su Render
1. render.com → accedi con GitHub → **New → Blueprint** → scegli il repository `sonora`.
   Render legge `render.yaml` e propone il servizio `sonora-api` (piano Free).
2. Ti chiede due valori:
   - `DATABASE_URL`: la stringa di Supabase del passo 2;
   - `FRONTEND_ORIGIN`: per ora scrivi `https://example.com` (lo correggi al passo 5).
3. **Apply**. Il primo deploy richiede 3–5 minuti. Alla fine copia l'indirizzo del servizio, tipo `https://sonora-api-ab12.onrender.com`.
4. Verifica: apri `https://sonora-api-ab12.onrender.com/api/v1/health` → deve mostrare `"status":"ok"`.
   Al primo avvio il server importa da solo il catalogo da Apple (circa 6 minuti, in sottofondo).

## 4. Pubblica l'app su Netlify
1. app.netlify.com → **Add new site → Import an existing project** → GitHub → `sonora`.
   Netlify legge `netlify.toml`: cartella `frontend`, comando e cartella di pubblicazione sono già impostati.
2. Prima di pubblicare, in *Environment variables* aggiungi:
   `SONORA_API_ORIGIN` = l'indirizzo Render del passo 3 (senza `/` finale).
3. **Deploy**. Poi in *Site configuration → Change site name* scegli un nome, per esempio `sonora-lollo` → `https://sonora-lollo.netlify.app`.

## 5. Collega i due
Su Render → servizio `sonora-api` → *Environment* → `FRONTEND_ORIGIN` = `https://sonora-lollo.netlify.app` (esatto, senza `/` finale) → *Save*.
Render riavvia il server. Senza questo passo accesso e registrazione rispondono "Origine della richiesta non consentita".

## 6. Aggiornamento automatico ogni giorno
Le anteprime Apple scadono dopo 7 giorni e la classifica cambia: GitHub le aggiorna ogni mattina.
1. Su Render → *Environment* → copia il valore di `INGEST_TOKEN` (generato automaticamente).
2. Su GitHub → repository → *Settings → Secrets and variables → Actions → New repository secret*:
   - `SONORA_API_URL` = indirizzo Render (passo 3)
   - `SONORA_INGEST_TOKEN` = il token appena copiato
3. *Actions → SONORA → Run workflow* per provarlo subito: deve finire con la spunta verde.

Questo aggiornamento tiene anche "sveglio" il database: secondo i termini attuali Supabase mette in pausa i progetti gratuiti inattivi da una settimana.

## 7. Installala sul telefono
Apri `https://sonora-lollo.netlify.app`:
- **Android (Chrome)**: menu ⋮ → *Installa app* (oppure Profilo → Installa l'app).
- **iPhone (Safari)**: pulsante Condividi → *Aggiungi alla schermata Home*.

---

## Cosa aspettarsi dal piano gratuito
- Se nessuno usa l'app per 15 minuti il server si spegne. Alla riapertura compare "SONORA si sta avviando" per circa un minuto, poi tutto riparte da solo.
- Il primo avvio dopo una pausa può far vedere il feed vuoto per qualche secondo: tira giù o tocca Riprova.
- Per toglierle: piano Starter di Render (7 $/mese), nessuna modifica al codice.

## Se qualcosa non va
| Sintomo | Causa probabile |
|---|---|
| Build Netlify fallisce con "Manca SONORA_API_ORIGIN" | Variabile del passo 4.2 assente o scritta male |
| "Origine della richiesta non consentita" all'accesso | `FRONTEND_ORIGIN` su Render diverso dall'indirizzo Netlify (passo 5) |
| Deploy Render fallisce con errore di connessione al database | Stringa Supabase sbagliata: usa *Session pooler* e controlla la password |
| Feed "catalogo vuoto" dopo 10 minuti | Guarda i *Logs* di Render: se Apple ha limitato le richieste, rilancia il workflow del passo 6 più tardi |
