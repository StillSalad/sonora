# Privacy, conservazione e cancellazione (bozza tecnica)

Non è un parere legale: va revisionato prima del lancio.

| Dato | Perché | Conservazione |
|---|---|---|
| Email, nome utente, nome visualizzato | Account | Fino alla cancellazione |
| Hash password (Argon2id) | Accesso | Fino alla cancellazione |
| Conferma età minima (solo data della conferma) | Consenso digitale (14 anni in Italia) | Fino alla cancellazione |
| Sessioni (hash del token) | Accesso | 30 giorni, revocabili |
| Audit log | Sicurezza | 12 mesi (job di pulizia in M8) |
| Generi e artisti scelti all'inizio | Personalizzare il feed | Sul dispositivo; con un account anche sul server, fino a modifica o cancellazione |
| "Non mi interessa", "Meno brani così", "Nascondi artista" | Escludere ciò che non vuoi | Fino ad Annulla o alla cancellazione dell'account |
| Voti sull'atmosfera dei brani (solo con account) | Mood della community | Fino a modifica o cancellazione dell'account |
| Brani mostrati nel feed (con un identificativo casuale del dispositivo, o l'account se connesso) | Non riproporre brani già visti | Usati per 14 giorni; pulizia automatica in M8 |

Cancellazione (`DELETE /api/v1/auth/account`): anonimizza subito email, username, nome, avatar e password, revoca tutte le sessioni e registra l'evento.
Un job (M8) eliminerà poi la riga utente: like, raccolte, eventi e preferenze cadono in cascata.
Esportazione dei dati: M8.

L'identificativo del dispositivo è un codice casuale generato dall'app e salvato solo nel browser (`localStorage`): non contiene dati personali e si azzera cancellando i dati del sito.
