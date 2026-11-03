import { stateImg } from "../lib/assets";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ButtonLink, NotActive, PageTitle, btnPrimary, field } from "../components/Pieces";
import { Icon } from "../components/Icon";
import { InstallButton } from "../components/InstallButton";
import { useApp } from "../context/AppContext";
import { api, ApiError } from "../lib/api";

export default function Profile() {
  const { user, authLoading, setUser } = useApp();
  const nav = useNavigate();

  async function logout() {
    try { await api("/auth/logout", { method: "POST" }); } finally { setUser(null); nav("/"); }
  }

  return (
    <>
      {authLoading ? <div className="h-32" /> : user ? (
        <>
          <PageTitle sub={`@${user.username}`}>{user.display_name}</PageTitle>
          <section aria-labelledby="dna" className="rounded-tile bg-surface">
            <h2 id="dna" className="sr-only">Music DNA</h2>
            <NotActive feature="music_dna" image={stateImg("music_dna")} title="Il tuo Music DNA">
              Generi, artisti, decenni e lingue che ascolti di più. Prende forma man mano che salvi e ascolti brani nel feed.
            </NotActive>
          </section>
        </>
      ) : (
        <>
          <PageTitle sub="Accedi per salvare brani e avere un feed costruito sui tuoi gusti.">Profilo</PageTitle>
          <div className="flex gap-3">
            <ButtonLink to="/accedi">Accedi</ButtonLink>
            <ButtonLink to="/registrati" variant="ghost">Crea account</ButtonLink>
          </div>
        </>
      )}

      <Settings />

      {user && (
        <section aria-labelledby="account" className="mt-8">
          <h2 id="account" className="mb-2 text-lg font-semibold">Account</h2>
          <div className="divide-y divide-surface2 rounded-tile bg-surface">
            <button onClick={logout} className="flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-surface2">
              <Icon name="logout" /> <span className="font-medium">Esci</span>
            </button>
            <DeleteAccount />
          </div>
        </section>
      )}
    </>
  );
}

function Settings() {
  const { theme, setTheme, meta } = useApp();
  return (
    <section aria-labelledby="settings" className="mt-8">
      <h2 id="settings" className="mb-2 text-lg font-semibold">Impostazioni</h2>
      <div className="divide-y divide-surface2 rounded-tile bg-surface">
        <button onClick={() => setTheme(theme === "dark" ? "light" : "dark")} aria-pressed={theme === "light"}
          className="flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-surface2">
          <Icon name={theme === "dark" ? "sun" : "moon"} className="text-secondary" />
          <span className="flex-1 font-medium">{theme === "dark" ? "Passa al tema chiaro" : "Passa al tema scuro"}</span>
        </button>
        <InstallButton />
        <div className="flex items-start gap-3 px-4 py-3">
          <Icon name="link" className="mt-0.5 text-muted" />
          <div className="text-sm">
            <p className="font-medium">Servizi musicali collegati</p>
            <p className="mt-0.5 text-muted">
              Il collegamento con Spotify, Apple Music e altri servizi non è ancora attivo. Quando lo sarà, avverrà
              sempre dalla pagina ufficiale del servizio: SONORA non ti chiederà mai la loro password.
            </p>
          </div>
        </div>
        <Link to="/privacy" className="flex items-center gap-3 px-4 py-3 hover:bg-surface2">
          <Icon name="external_link" className="text-muted" /> <span className="font-medium">Privacy e dati</span>
        </Link>
      </div>
      {meta && <p className="mt-3 text-xs text-muted">SONORA {meta.version}</p>}
    </section>
  );
}

function DeleteAccount() {
  const { setUser } = useApp();
  const nav = useNavigate();
  const [open, setOpen] = useState(false);
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setError(null);
    try {
      await api("/auth/account", { method: "DELETE", json: { password } });
      setUser(null);
      nav("/", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Eliminazione non riuscita.");
    } finally { setBusy(false); }
  }

  if (!open)
    return (
      <button onClick={() => setOpen(true)} className="flex w-full items-center gap-3 px-4 py-3 text-left text-danger hover:bg-surface2">
        <span className="w-6" /> <span className="font-medium">Elimina account</span>
      </button>
    );
  return (
    <form onSubmit={submit} className="flex flex-col gap-3 px-4 py-4">
      <p className="text-sm">
        L’account viene anonimizzato subito e le sessioni chiuse. Preferiti, raccolte e attività vengono cancellati.
        Non si può annullare.
      </p>
      <label htmlFor="del-pw" className="text-sm font-medium">Conferma con la password</label>
      <input id="del-pw" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} className={field} />
      {error && <p role="alert" className="text-sm text-danger">{error}</p>}
      <div className="flex gap-3">
        <button type="submit" disabled={!password || busy} className={`${btnPrimary} bg-danger`}>{busy ? "Eliminazione…" : "Elimina definitivamente"}</button>
        <button type="button" onClick={() => setOpen(false)} className="rounded-full px-4 font-semibold text-muted">Annulla</button>
      </div>
    </form>
  );
}
