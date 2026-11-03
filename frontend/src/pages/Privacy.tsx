import { PageTitle } from "../components/Pieces";

export default function Privacy() {
  return (
    <article className="max-w-prose">
      <PageTitle back>Privacy e dati</PageTitle>
      <div className="flex flex-col gap-4 leading-relaxed text-ink/90">
        <p>Versione di sviluppo: questo testo descrive come funziona il codice, non sostituisce un’informativa revisionata da un legale prima del lancio.</p>
        <h2 className="text-lg font-semibold">Cosa salviamo</h2>
        <p>Email, nome utente, nome visualizzato, password cifrata con Argon2 e la conferma di avere almeno 14 anni. Non chiediamo data di nascita, telefono o posizione.</p>
        <h2 className="text-lg font-semibold">Accesso</h2>
        <p>Usiamo un solo cookie tecnico di sessione, non leggibile da script e revocabile. Nessun cookie pubblicitario o di profilazione di terze parti.</p>
        <h2 className="text-lg font-semibold">Servizi musicali</h2>
        <p>Copertine, anteprime e link arriveranno dai provider autorizzati e restano presso di loro. SONORA non ospita audio e non ti chiederà mai la password di Spotify, Apple o Google.</p>
        <h2 className="text-lg font-semibold">Cancellazione</h2>
        <p>Da Profilo › Elimina account cancelli l’account: i dati personali vengono anonimizzati subito e le sessioni chiuse.</p>
      </div>
    </article>
  );
}
