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
- Uso: classifiche di più paesi (`CHART_COUNTRIES`, predefinito Italia, Stati Uniti, Regno Unito, Spagna, Germania; la Francia è stata tolta su richiesta).
  Ogni brano in almeno una classifica diventa `popularity_class = popular`; tutte le posizioni restano in `popularity_sources`.
  La classifica del paese dell'app pesa di più (1.0 contro 0.85). I brani esteri vengono cercati sullo store italiano:
  se lì non esistono vengono scartati. Chi esce da tutte le classifiche torna `unknown`. Se un brano era entrato solo da classifiche non più configurate
  viene nascosto (`hidden_reason = chart_removed:…`), a meno che qualcuno non lo abbia tra i Mi piace. Confermare che questo uso rientri nei termini Marketing Tools.

## MusicBrainz (pronto, disattivato di default)
- Solo metadati: cerca l'ISRC di un brano. Accettato solo con corrispondenza univoca (punteggio 100, durata entro 2 s, un solo ISRC).
- Richiede `MUSICBRAINZ_CONTACT` per lo User-Agent; massimo 1 richiesta al secondo.

## Spotify, YouTube Music, Lyra
Non integrati. Vedi `LEGAL_AND_PROVIDER_RULES.md` e la matrice in `ARCHITECTURE.md` (Milestone 7).

## La regola 80/20 con questi dati
Apple non fornisce un indice di "brano poco conosciuto". SONORA quindi riempie il 20% "scoperta" con brani **fuori
dalle classifiche attuali**, e lo dice esattamente così nella spiegazione ("Scoperta fuori dalle classifiche attuali").
Non affermiamo che quei brani siano sconosciuti: la loro classe di popolarità resta `unknown`.

## Mood
Apple non fornisce l'atmosfera dei brani. I mood di SONORA vengono solo dai voti degli utenti con account
("Che atmosfera ha?", massimo 2 per brano): un mood diventa tag quando ha almeno `MOOD_MIN_VOTES` voti (predefinito 1)
e la maggioranza dei votanti. La pagina mood lo dichiara ("Atmosfera votata da chi ascolta su SONORA").

## Condividi come storia
L'immagine generata contiene la copertina fornita da Apple insieme al link al brano. Prima di un lancio pubblico
verificare che questo uso rientri nelle linee guida per i contenuti promozionali Apple.
