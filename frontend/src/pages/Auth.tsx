import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { PageTitle, btnPrimary, field } from "../components/Pieces";
import { useApp } from "../context/AppContext";
import { api, ApiError, type User } from "../lib/api";

function safeNext(v: string | null) {
  return v && v.startsWith("/") && !v.startsWith("//") ? v : "/profilo";
}

function FieldError({ id, msg }: { id: string; msg?: string }) {
  return msg ? <p id={id} className="mt-1.5 text-sm text-danger">{msg}</p> : null;
}

export function Login() {
  const { user, setUser, backend } = useApp();
  const [params] = useSearchParams();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  if (user) return <Navigate to={safeNext(params.get("dopo"))} replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setError(null);
    try {
      setUser(await api<User>("/auth/login", { method: "POST", json: { email, password } }));
      nav(safeNext(params.get("dopo")), { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Accesso non riuscito.");
    } finally { setBusy(false); }
  }

  return (
    <div className="mx-auto max-w-sm">
      <PageTitle back>Accedi</PageTitle>
      <form onSubmit={submit} className="flex flex-col gap-4" noValidate>
        <div>
          <label htmlFor="email" className="mb-1.5 block text-sm font-medium">Email</label>
          <input id="email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} className={field} />
        </div>
        <div>
          <label htmlFor="password" className="mb-1.5 block text-sm font-medium">Password</label>
          <input id="password" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} className={field} />
        </div>
        {error && <p role="alert" className="text-sm text-danger">{error}</p>}
        <button type="submit" disabled={busy || backend !== "ok"} className={btnPrimary}>{busy ? "Accesso…" : "Accedi"}</button>
        <p className="text-center text-sm text-muted">Non hai un account? <Link to="/registrati" className="font-semibold text-secondary">Creane uno</Link></p>
      </form>
    </div>
  );
}

export function Register() {
  const { user, setUser, backend } = useApp();
  const nav = useNavigate();
  const [form, setForm] = useState({ email: "", username: "", display_name: "", password: "", confirm_min_age: false });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  if (user) return <Navigate to="/profilo" replace />;

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value }));

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setError(null); setErrors({});
    try {
      setUser(await api<User>("/auth/register", { method: "POST", json: form }));
      nav("/profilo", { replace: true });
    } catch (err) {
      if (err instanceof ApiError) {
        setErrors(Object.fromEntries(err.fields.map((f) => [f.field, f.message.replace(/^Value error, /, "")])));
        setError(err.message);
      } else setError("Registrazione non riuscita.");
    } finally { setBusy(false); }
  }

  const input = (k: "email" | "username" | "display_name" | "password", label: string, type: string, auto: string, hint?: string) => (
    <div>
      <label htmlFor={k} className="mb-1.5 block text-sm font-medium">{label}</label>
      <input id={k} type={type} autoComplete={auto} required value={form[k]} onChange={set(k)}
        aria-invalid={!!errors[k]} aria-describedby={`${k}-err ${k}-hint`} className={field} />
      {hint && <p id={`${k}-hint`} className="mt-1.5 text-xs text-muted">{hint}</p>}
      <FieldError id={`${k}-err`} msg={errors[k]} />
    </div>
  );

  return (
    <div className="mx-auto max-w-sm">
      <PageTitle back sub="Serve per salvare brani, creare raccolte e costruire il tuo Music DNA.">Crea account</PageTitle>
      <form onSubmit={submit} className="flex flex-col gap-4" noValidate>
        {input("display_name", "Nome", "text", "nickname")}
        {input("username", "Nome utente", "text", "username", "Minuscole, numeri, punto o trattino basso.")}
        {input("email", "Email", "email", "email")}
        {input("password", "Password", "password", "new-password", "Almeno 10 caratteri.")}
        <label className="flex items-start gap-3 text-sm">
          <input type="checkbox" checked={form.confirm_min_age} onChange={set("confirm_min_age")} className="mt-0.5 h-5 w-5 accent-[rgb(var(--primary))]" />
          <span>Ho almeno 14 anni e ho letto <Link to="/privacy" className="font-semibold text-secondary">come SONORA usa i miei dati</Link>.</span>
        </label>
        {error && <p role="alert" className="text-sm text-danger">{error}</p>}
        <button type="submit" disabled={busy || !form.confirm_min_age || backend !== "ok"} className={btnPrimary}>
          {busy ? "Creazione…" : "Crea account"}
        </button>
        <p className="text-center text-sm text-muted">Hai già un account? <Link to="/accedi" className="font-semibold text-secondary">Accedi</Link></p>
      </form>
    </div>
  );
}
