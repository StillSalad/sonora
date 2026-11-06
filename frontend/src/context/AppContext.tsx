import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { api, ApiError, type Meta, type User } from "../lib/api";
import { syncPrefs } from "../lib/prefs";

type BackendState = "checking" | "ok" | "waking" | "unreachable";
type Theme = "dark" | "light";

type Ctx = {
  meta: Meta | null;
  backend: BackendState;
  online: boolean;
  user: User | null;
  authLoading: boolean;
  theme: Theme;
  setTheme: (t: Theme) => void;
  retry: () => void;
  refreshUser: () => Promise<void>;
  setUser: (u: User | null) => void;
};

const AppCtx = createContext<Ctx | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [backend, setBackend] = useState<BackendState>("checking");
  const [online, setOnline] = useState(typeof navigator === "undefined" ? true : navigator.onLine);
  const [user, setUser] = useState<User | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [theme, setThemeState] = useState<Theme>(
    (typeof document !== "undefined" && document.documentElement.dataset.theme === "light") ? "light" : "dark",
  );

  const refreshUser = useCallback(async () => {
    try {
      setUser((await api<{ user: User | null }>("/auth/session")).user);
    } catch (e) {
      if (!(e instanceof ApiError) || e.status !== 0) setUser(null);
    } finally {
      setAuthLoading(false);
    }
  }, []);

  // Il server gratuito si spegne quando non è usato e impiega circa un minuto a ripartire:
  // ritentiamo per ~2 minuti mostrando "si sta avviando" prima di dichiararlo irraggiungibile.
  const attempt = useRef(0);
  const load = useCallback(async () => {
    setBackend((b) => (b === "waking" ? b : "checking"));
    try {
      setMeta(await api<Meta>("/meta"));
      attempt.current = 0;
      setBackend("ok");
      await refreshUser();
    } catch (e) {
      const transient = e instanceof ApiError && (e.status === 0 || e.status >= 500);
      if (transient && attempt.current < 8 && navigator.onLine) {
        attempt.current += 1;
        setBackend("waking");
        setTimeout(() => void loadRef.current(), 15000);
      } else {
        attempt.current = 0;
        setBackend("unreachable");
        setAuthLoading(false);
      }
    }
  }, [refreshUser]);
  const loadRef = useRef(load);
  loadRef.current = load;

  useEffect(() => { void load(); }, [load]);
  useEffect(() => { if (user) void syncPrefs(user); }, [user?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const on = () => { setOnline(true); void load(); };
    const off = () => setOnline(false);
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    return () => { window.removeEventListener("online", on); window.removeEventListener("offline", off); };
  }, [load]);

  const setTheme = useCallback((t: Theme) => {
    setThemeState(t);
    document.documentElement.dataset.theme = t;
    document.querySelector('meta[name="theme-color"]')?.setAttribute("content", t === "light" ? "#F6F5FB" : "#0B0D14");
    try { localStorage.setItem("sonora-theme", t); } catch { /* storage non disponibile */ }
  }, []);

  const value = useMemo(
    () => ({ meta, backend, online, user, authLoading, theme, setTheme, retry: () => { attempt.current = 0; void load(); }, refreshUser, setUser }),
    [meta, backend, online, user, authLoading, theme, setTheme, load, refreshUser],
  );
  return <AppCtx.Provider value={value}>{children}</AppCtx.Provider>;
}

export function useApp() {
  const c = useContext(AppCtx);
  if (!c) throw new Error("useApp fuori da AppProvider");
  return c;
}
