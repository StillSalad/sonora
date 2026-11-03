# Provider e diritti (stato Milestone 3)

Checklist tecnica, non parere legale. Rileggere i termini aggiornati prima di un lancio pubblico o commerciale.

## Apple — iTunes Search API (attivo)
- Endpoint: `https://itunes.apple.com/search` e `/lookup`. Nessuna chiave, nessun account Apple Developer.
- Cosa usiamo: titolo, artista, album, durata, genere, copertina, anteprima di 30 secondi, link ad Apple Music.
- Condizioni (Apple Performance Partners, Search API):
  - contenuti promozionali (anteprime, copertine) solo per promuovere i contenuti dello store, non come intrattenimento a sé;
  - l'anteprima va mostrata vicino a un badge dello store → ogni scheda ha "Ascolta su Apple Music" accanto al play;
  - circa 20 richieste al minuto → `Throttle(3.1 s)` nell'adapter, catalogo salvato nel database, ricerche ripetute in cache 24 h.
- Implementazione: `app/providers/itunes.py`. Ogni anteprima salva provider, territorio (`STORE_COUNTRY`), durata massima 30 s,
  riferimento ai termini e scadenza a 7 giorni: dopo la scadenza l'URL non viene più mostrato finché il job di import non la riverifica.
- L'audio non viene mai scaricato né messo in cache: il browser lo riproduce direttamente dai server Apple.
- **Da fare prima del lancio**: sostituire il link testuale con il badge ufficiale "Listen on Apple Music" scaricato da
  Apple Marketing Tools e rispettarne le linee guida grafiche.

## Apple — classifiche Marketing Tools (attivo, segnale di popolarità)
- `https://rss.marketingtools.apple.com/api/v2/{paese}/music/most-played/100/songs.json` (con ripiego sul vecchio host
  `rss.applemarketingtools.com`). Nessuna chiave.
- Uso: la posizione in classifica diventa `popularity_class = popular`, con rango, paese e data in `popularity_sources`.
  Chi esce dalla classifica torna `unknown`. Confermare che questo uso rientri nei termini Marketing Tools.

## MusicBrainz (pronto, disattivato di default)
- Solo metadati: cerca l'ISRC di un brano. Accettato solo con corrispondenza univoca (punteggio 100, durata entro 2 s, un solo ISRC).
- Richiede `MUSICBRAINZ_CONTACT` per lo User-Agent; massimo 1 richiesta al secondo.

## Spotify, YouTube Music, Lyra
Non integrati. Vedi `LEGAL_AND_PROVIDER_RULES.md` e la matrice in `ARCHITECTURE.md` (Milestone 7).

## La regola 80/20 con questi dati
Apple non fornisce un indice di "brano poco conosciuto". SONORA quindi riempie il 20% "scoperta" con brani **fuori
dalle classifiche attuali**, e lo dice esattamente così nella spiegazione ("Scoperta fuori dalle classifiche attuali").
Non affermiamo che quei brani siano sconosciuti: la loro classe di popolarità resta `unknown`.
