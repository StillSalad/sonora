import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { sendEvent, type Track } from "../lib/api";

/** Player delle anteprime: idle → loading → playing ⇄ paused → ended | error.
 *  Due elementi audio che si alternano: mentre uno suona, l'altro precarica il brano successivo,
 *  così scorrendo l'audio parte subito. Stop forzato alla durata consentita (30 s),
 *  nessun audio prima di un gesto, pausa quando l'app va in background. */
export type PlayerState = "idle" | "loading" | "playing" | "paused" | "ended" | "error";

type Ctx = {
  state: PlayerState; trackId: string | null; progress: number; muted: boolean; unlocked: boolean;
  play: (t: Track, surface?: string) => void; toggle: (t: Track, surface?: string) => void;
  stop: (reason?: "skip" | "silent") => void; setMuted: (m: boolean) => void; preload: (t: Track | undefined) => void;
};
const PlayerCtx = createContext<Ctx | null>(null);

// WAV vuoto: serve solo a "sbloccare" il secondo lettore durante il primo tocco (richiesto da iOS)
const SILENT = "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=";

export function PlayerProvider({ children }: { children: ReactNode }) {
  const pool = useRef<HTMLAudioElement[]>([]);
  const activeIdx = useRef(0);
  const current = useRef<{ track: Track; limit: number; surface?: string } | null>(null);
  const [state, setState] = useState<PlayerState>("idle");
  const [trackId, setTrackId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [muted, setMutedState] = useState(false);
  const [unlocked, setUnlocked] = useState(false);
  const unlockedRef = useRef(false);

  const elements = useCallback(() => {
    if (!pool.current.length) {
      pool.current = [0, 1].map(() => {
        const a = new Audio();
        a.preload = "none";
        const isActive = () => pool.current[activeIdx.current] === a;
        a.addEventListener("playing", () => isActive() && setState("playing"));
        a.addEventListener("waiting", () => isActive() && setState("loading"));
        a.addEventListener("pause", () => isActive() && setState((s) => (s === "ended" || s === "idle" ? s : "paused")));
        a.addEventListener("error", () => { if (isActive() && current.current && a.src && !a.src.startsWith("data:")) setState("error"); });
        a.addEventListener("timeupdate", () => {
          const c = current.current;
          if (!c || !isActive()) return;
          setProgress(Math.min(1, a.currentTime / c.limit));
          if (a.currentTime >= c.limit) a.dispatchEvent(new Event("ended"));
        });
        a.addEventListener("ended", () => {
          const c = current.current;
          if (!isActive() || !c) return;
          a.pause();
          setState("ended"); setProgress(1);
          sendEvent(c.track.id, "preview_complete", { listened_ms: Math.round(c.limit * 1000), source_surface: c.surface });
        });
        return a;
      });
    }
    return pool.current;
  }, []);

  const active = () => elements()[activeIdx.current];
  const idle = () => elements()[1 - activeIdx.current];

  const stop = useCallback((reason: "skip" | "silent" = "silent") => {
    const a = pool.current[activeIdx.current], c = current.current;
    if (a && c && reason === "skip" && !a.paused && a.currentTime < c.limit * 0.8) {
      sendEvent(c.track.id, "skip", { listened_ms: Math.round(a.currentTime * 1000), source_surface: c.surface });
    }
    if (a) { a.pause(); a.removeAttribute("src"); a.load(); }
    current.current = null;
    setTrackId(null); setState("idle"); setProgress(0);
  }, []);

  const preload = useCallback((t: Track | undefined) => {
    const url = t?.preview.url;
    if (!url || current.current?.track.id === t!.id) return;
    const b = idle();
    if (b.src !== url) { b.preload = "auto"; b.src = url; b.load(); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const play = useCallback((t: Track, surface?: string) => {
    const url = t.preview.url;
    if (!url) return;
    if (!unlockedRef.current) {
      // primo gesto: sblocca anche il secondo lettore, così i brani successivi partono da soli
      unlockedRef.current = true;
      setUnlocked(true);
      const b = idle();
      if (!b.src) { b.muted = true; b.src = SILENT; b.play().then(() => b.pause()).catch(() => {}).finally(() => { b.muted = muted; }); }
    }
    let a = active();
    if (current.current?.track.id !== t.id) {
      stop("skip");
      const b = idle();
      if (b.src !== url) { b.src = url; }
      activeIdx.current = 1 - activeIdx.current; // il lettore che aveva già caricato diventa quello attivo
      a = b;
      a.muted = muted;
      current.current = { track: t, limit: Math.min(t.preview.duration_seconds ?? 30, 30), surface };
      setTrackId(t.id); setProgress(0);
      sendEvent(t.id, "preview_start", { source_surface: surface });
    } else if (state === "ended") {
      a.currentTime = 0;
    }
    setState("loading");
    a.play().catch(() => setState("error"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stop, state, muted]);

  const toggle = useCallback((t: Track, surface?: string) => {
    if (trackId === t.id && (state === "playing" || state === "loading")) active().pause();
    else play(t, surface);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trackId, state, play]);

  const setMuted = useCallback((m: boolean) => {
    setMutedState(m);
    pool.current.forEach((a) => { a.muted = m; });
  }, []);

  useEffect(() => () => { pool.current.forEach((a) => a.pause()); }, []);
  useEffect(() => {
    const onHide = () => { if (document.hidden) pool.current.forEach((a) => a.pause()); };
    document.addEventListener("visibilitychange", onHide);
    return () => document.removeEventListener("visibilitychange", onHide);
  }, []);

  const value = useMemo(() => ({ state, trackId, progress, muted, unlocked, play, toggle, stop, setMuted, preload }),
    [state, trackId, progress, muted, unlocked, play, toggle, stop, setMuted, preload]);
  return <PlayerCtx.Provider value={value}>{children}</PlayerCtx.Provider>;
}

export function usePlayer() {
  const c = useContext(PlayerCtx);
  if (!c) throw new Error("usePlayer fuori da PlayerProvider");
  return c;
}
