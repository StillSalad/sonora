# Changelog

## 0.5.0 — Personalizzazione (2026-11-05)
### Aggiunto
- Scelta iniziale: almeno 3 generi, poi artisti di quei generi dal catalogo (con la copertina del loro brano più noto); si può saltare e modificare da Profilo. Salvata sul dispositivo e, con un account, sul server.
- Quota personale nel feed: una posizione su due va ai gusti scelti o ai Mi piace, con spiegazione ("Perché hai scelto Jazz").
- Gesti sulla copertina: tocco = play/pausa, doppio tocco = Mi piace con cuore animato, tieni premuto = menu. Pulsante ⋯ equivalente per chi non usa i gesti.
- "Non fa per me": Non mi interessa, Meno brani di un genere, Nascondi artista, con Annulla. Per account o dispositivo.
- Partenza istantanea: due lettori audio alternati, il brano successivo si precarica; copertine dei due successivi precaricate.
- "Altri brani così": mini feed da un brano (stesso artista, stesso genere, stessa atmosfera).
- "Che atmosfera ha?": voto della community su fino a 2 mood; le pagine mood si riempiono con i brani votati.
- Condividi come storia: immagine 1080×1920 con copertina, titolo, artista e logo.
- Scoperta del giorno in testa al feed alla prima apertura della giornata.
- Icone: altre azioni, spunta, chiudi. Migrazione 0004.

### Modificato
- Tolta la classifica francese; i brani arrivati solo da lì vengono nascosti (salvo Mi piace).

### Corretto durante la prova nel browser
- Sul telefono la barra di navigazione copriva il pulsante "Avanti" della scelta iniziale: ora la scelta è a tutto schermo.
- I menu dal basso finivano sotto la barra di navigazione (voci in fondo non toccabili): ora sono disegnati sopra tutta l'app.
- La scoperta del giorno spariva se era anche tra i brani del feed: ora resta in cima e il doppione viene tolto; arriva insieme alla prima pagina, senza spostare i brani mentre si scorre.
- "Ascolta su Apple Music" usciva dal bordo destro sui telefoni stretti.

### Verificato
- 64 test backend (anche su PostgreSQL, ripetuti 3 volte), 25 test frontend.
- Prova nel browser (Chromium, schermo da telefono): scelta iniziale, feed personalizzato, tocco/doppio tocco/tieni premuto, voto mood e pagina mood, Non mi interessa (il brano non ricompare in 3 aperture), Nascondi artista, Altri brani così, storia 1080×1920, scoperta del giorno, desktop.

## 0.4.0 — Feed più vario (2026-11-03)
### Corretto (segnalazione: "si ripetono spesso le canzoni")
- Memoria tra sessioni: i brani mostrati negli ultimi 3 giorni non tornano finché c'è altra musica; dal 4° al 14° giorno sono solo penalizzati. Vale per dispositivo (identificativo casuale) e per account.
- Ordine casuale pesato per sessione al posto di un ordine quasi fisso: la prima canzone cambia a ogni apertura.
- Brani popolari da 6 classifiche (Italia, Stati Uniti, Regno Unito, Spagna, Francia, Germania) invece della sola italiana.
- Scoperte pescate a caso da tutto il catalogo, non sempre dagli stessi ~300 brani.
- Lo stesso artista non torna prima di 6 brani (prima 3).
- Il server reimporta da solo all'avvio se le classifiche hanno più di 20 ore o ne manca una configurata.

### Misurato
Simulazione di 7 aperture × 20 brani: prima 52 brani diversi su 140 (88 ripetizioni), ora 140 su 140 (0 ripetizioni); primo brano diverso 7 volte su 7 (prima 4).

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
