# MASTER PROMPT — SONORA
## Istruzioni per Claude: costruzione di un prodotto reale, non di un mockup

Agisci come un team senior composto da product designer, UX engineer, frontend engineer,
backend engineer, database architect, QA engineer e consulente di integrazioni API.
Il proprietario del progetto è un principiante: spiega le operazioni in modo semplice,
ma produci codice professionale, modulare, testabile e documentato.

### A. Visione
Costruisci SONORA, una Progressive Web App mobile-first dedicata alla scoperta musicale.
SONORA non deve diventare un servizio di streaming autonomo. Deve mostrare catalogo,
metadati, copertine e anteprime esclusivamente quando l'utilizzo è consentito dal provider
e dai relativi diritti. Se un'anteprima non è disponibile, mostra la scheda e un link esterno.

### B. Regola editoriale fondamentale: 80/20
Il feed For You deve puntare a:
- 80% brani famosi / popolari / riconoscibili;
- 20% brani meno conosciuti / emergenti / discovery.

Calcolare la quota su una finestra mobile di 50 brani (40 popolari, 10 discovery), con
tolleranza quando il catalogo filtrato non contiene abbastanza elementi. Non inventare
popolarità: usare segnali documentati, ad esempio classifiche ufficiali disponibili,
popolarità esposta legalmente dal provider, chart rank, trend verificabili e dati aggregati
interni. Conservare `popularity_score`, `popularity_confidence`, `popularity_sources`,
`popularity_updated_at`. Se il punteggio non è attendibile, classificare come `unknown`
e non fingere che sia famoso o sconosciuto. Non ripetere lo stesso brano nella sessione
e limitare ripetizioni di artista consecutivi.

### C. Identità visiva
Usare gli asset in `assets/`. Palette:
#0B0D14 background, #151925 surface, #202638 secondary surface,
#8B5CF6 primary, #38BDF8 secondary, #E879F9 accent,
#F5F6FA text, #969DB0 muted.
Stile premium, scuro, editoriale, pulito e riconoscibile. Le copertine sono protagoniste.
Non copiare il layout o il branding di Spotify, TikTok o Pinterest.
Supportare dark e light theme, ma dark è il default.
Non inserire testo dentro immagini decorative. Usare SVG separati, non spritesheet.

### D. Stack
Frontend: React + TypeScript + Vite + Tailwind CSS.
PWA: manifest, service worker, install prompt, cache prudente di shell e metadati.
Backend: Python + FastAPI.
Database: PostgreSQL + SQLAlchemy + Alembic.
Cache/queue: Redis solo quando necessario.
Test: pytest backend, Vitest/React Testing Library frontend, Playwright per flussi end-to-end.
Deployment: configurabile tramite environment variables; non fissare provider a pagamento.

### E. Aree prodotto
1. Home / For You: feed verticale, una traccia per card, preview autorizzata, like,
   salva, skip, share, add-to-platform.
2. Explore: generi, sottogeneri, mood, decenni, lingue, paesi, situazioni, strumenti,
   caratteristiche vocali e hashtag.
3. Search: titolo, artista, album, tag, combinazioni di filtri.
4. Collections: moodboard/collezioni visuali con brani, tag, copertina, descrizione,
   visibilità privata/pubblica e collaborazione in una fase successiva.
5. Community: profili, follow, raccolte pubbliche, reazioni e segnalazioni.
6. Profile / My Music DNA: gusti, artisti, tag, decenni e lingue preferite.
7. Connect: collegamenti esterni e integrazioni account consentite.
8. Admin: gestione catalogo, provider, tag, duplicati, preview rights, segnalazioni e metriche.

### F. Catalogo multi-provider
Creare un modello canonico interno per artisti, album e tracce.
Ogni provider ha ID esterni separati in `provider_tracks` / tabelle equivalenti.
Deduplicare con ISRC quando disponibile, poi confrontare titolo normalizzato, artista,
durata e release; mai fondere automaticamente corrispondenze incerte senza review.
Conservare provenienza e timestamp per ogni campo importante.
Usare API ufficiali e rispettarne rate limit, attribuzione, caching, territorio e termini.
Non effettuare scraping non autorizzato, non estrarre audio da servizi, non aggirare DRM,
non ospitare file musicali protetti senza licenza.
Spotify: non progettare il prodotto intorno a preview URL deprecati o all'uso autonomo
di clip Spotify. Usare link esterni e funzioni consentite dalle policy correnti.
Apple Music: usare MusicKit/API secondo autorizzazioni, token e condizioni correnti.
MusicBrainz: usare per metadati e identificazione nel rispetto delle condizioni e rate limit.
YouTube Music: non presumere l'esistenza di un'API pubblica ufficiale per tutte le funzioni;
usare link esterni o integrazioni ufficialmente disponibili.
Lyra: implementazione tramite adapter configurabile; non inventare endpoint. Se il proprietario
fornisce schema URL/API, implementare solo quello.

### G. Preview system
Ogni traccia ha preview state:
AVAILABLE, UNAVAILABLE, EXTERNAL_ONLY, RIGHTS_PENDING, BLOCKED.
Un record preview deve conservare provider, URL se consentito, durata, territorio,
scadenza, licenza/terms reference e timestamp verifica.
Non scaricare né cacheare il file audio a meno che il contratto lo consenta esplicitamente.
Non esporre preview non autorizzate.
Il player deve fermare la preview alla durata consentita e gestire errori, cambio brano,
pausa, mute e stato di caricamento.
Non avviare audio automaticamente prima di un gesto utente se browser/device lo impedisce.

### H. Tag Engine
Un brano può avere molti tag. Ogni tag ha categoria, slug, label, lingua, descrizione,
relazioni con altri tag, origine e livello di confidenza.
Distinguere tag editoriali verificati, tag provider, tag automatici e tag suggeriti dagli utenti.
Non presentare inferenze come fatti. Moderare tag pubblici e prevenire spam.
Supportare filtri AND/OR e combinazioni del tipo Italian Pop + Nostalgic + 2010s.

### I. Recommendation engine
Versione 1: algoritmo deterministico e spiegabile, non serve un modello AI costoso.
Segnali: like, salvataggi, ascolto preview, skip, artisti/tag seguiti, ricerche, aggiunte
esterne se disponibili e autorizzate.
Skip non equivale automaticamente a dislike.
Diversificare artisti, generi, epoche e mood.
Riservare il 20% discovery, evitare ripetizioni, applicare filtri di esclusione e
rispettare il rapporto 80/20 sulla finestra mobile.
Mostrare motivazioni semplici: "Perché segui #IndiePop", "Popolare in Italia",
"Scoperta fuori dai tuoi soliti generi".
Fornire controlli: più simili, meno simili, nascondi artista, nascondi tag, reset preferenze.

### J. PWA e offline
Installabile su Android, iOS e desktop dove supportato.
Service worker per app shell, asset statici e metadati selezionati.
Non salvare audio protetto offline senza permesso.
Mostrare stato online/offline e retry.
Usare immagini responsive e lazy loading.
Garantire accessibilità, contrasto, focus keyboard e reduced motion.

### K. Sicurezza e privacy
OAuth per servizi esterni; mai chiedere o conservare password Spotify/Apple/Google.
Proteggere segreti nel backend, mai nel bundle frontend.
Rate limiting, input validation, CSRF/session strategy appropriata, secure headers,
ruoli admin, audit log, backup e gestione cancellazione account.
Privacy by design e GDPR: minimizzazione, consenso, esportazione/cancellazione dati,
informative e retention documentata. Non raccogliere dati non necessari.
Moderazione, segnalazione, blocco utenti e protezione degli utenti giovani.

### L. Deliverable richiesti
- Codice completo frontend e backend.
- Migrazioni database.
- `.env.example` senza segreti.
- Seed demo con dati fittizi chiaramente marcati.
- Test automatici.
- README con installazione passo passo per principiante.
- Documentazione API.
- Documentazione provider e diritti.
- Asset manifest.
- Deployment guide.
- Admin dashboard.
- Nessuna funzione finta presentata come funzionante.

### M. Metodo di lavoro obbligatorio
Non generare tutto in un'unica risposta o in un unico file.
Procedi per milestone:
1. Architecture + data model + UX map + risk register.
2. Foundation PWA + design system + navigation + auth scaffolding.
3. Catalog adapters + canonical data model + search.
4. Feed + authorized preview player + 80/20 mixer.
5. Tag engine + Explore + collections.
6. Recommendation engine + profile.
7. External integrations + community.
8. Admin + security hardening + tests + deployment.

Prima di ogni milestone:
- elenca i file che creerai/modificherai;
- implementa il codice;
- esegui test e correggi errori;
- aggiorna README e changelog;
- spiega come avviare e verificare la fase.

Se mancano API key, OAuth credentials o licenze, crea adapter e mock mode chiaramente
separati, con interfacce reali ma senza fingere di avere accesso al provider.
Non inserire chiavi inventate. Non sostituire integrazioni reali con pulsanti decorativi.
Prima di scrivere molto codice, presenta la struttura e le decisioni architetturali.
