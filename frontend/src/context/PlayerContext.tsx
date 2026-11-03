import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { sendEvent, type Track } from "../lib/api";

/** Macchina a stati del player anteprime: idle → loading → playing ⇄ paused → ended | error.
 *  Un solo elemento audio, stop forzato alla durata consentita, nessun audio prima di un gesto. */
export type PlayerState = "idle" | "loading" | "playing" | "paused" | "ended" | "error";

type Ctx = {
  state: PlayerState; trackId: string | null; progress: number; muted: boolean; unlocked: boolean;
  play: (t: Track, surface?: string) => void; toggle: (t: Track, surface?: string) => void;
  stop: (reason?: "skip" | "silent") => void; setMuted: (m: boolean) => void;
};
const PlayerCtx = createContext<Ctx | null>(null);

export function PlayerProvider({ children }: { children: ReactNode }) {
  const audio = useRef<HTMLAudioElement | null>(null);
  const current = useRef<{ track: Track; limit: number; surface?: string } | null>(null);
  const [state, setState] = useState<PlayerState>("idle");
  const [trackId, setTrackId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [muted, setMutedState] = useState(false);
  const [unlocked, setUnlocked] = useState(false);

  const el = useCallback(() => {
    if (!audio.current) {
      const a = new Audio();
      a.preload = "none";
      a.addEventListener("playing", () => setState("playing"));
      a.addEventListener("waiting", () => setState("loading"));
      a.addEventListener("pause", () => setState((s) => (s === "ended" || s === "idle" ? s : "paused")));
      a.addEventListener("error", () => { if (a.src) setState("error"); });
      a.addEventListener("timeupdate", () => {
        const c = current.current;
        if (!c) return;
        setProgress(Math.min(1, a.currentTime / c.limit));
        if (a.currentTime >= c.limit) a.dispatchEvent(new Event("ended"));
      });
      a.addEventListener("ended", () => {
        const c = current.current;
        a.pause();
        setState("ended"); setProgress(1);
        if (c) sendEvent(c.track.id, "preview_complete", { listened_ms: Math.round(c.limit * 1000), source_surface: c.surface });
      });
      audio.current = a;
    }
    return audio.current;
  }, []);

  const stop = useCallback((reason: "skip" | "silent" = "silent") => {
    const a = audio.current, c = current.current;
    if (a && c && reason === "skip" && !a.paused && a.currentTime < c.limit * 0.8) {
      sendEvent(c.track.id, "skip", { listened_ms: Math.round(a.currentTime * 1000), source_surface: c.surface });
    }
    if (a) { a.pause(); a.removeAttribute("src"); a.load(); }
    current.current = null;
    setTrackId(null); setState("idle"); setProgress(0);
  }, []);

  const play = useCallback((t: Track, surface?: string) => {
    if (!t.preview.url) return;
    const a = el();
    if (current.current?.track.id !== t.id) {
      stop("skip");
      current.current = { track: t, limit: Math.min(t.preview.duration_seconds ?? 30, 30), surface };
      a.src = t.preview.url;
      setTrackId(t.id); setProgress(0);
      sendEvent(t.id, "preview_start", { source_surface: surface });
    } else if (state === "ended") {
      a.currentTime = 0;
    }
    setState("loading");
    setUnlocked(true);
    a.play().catch(() => setState("error"));
  }, [el, stop, state]);

  const toggle = useCallback((t: Track, surface?: string) => {
    if (trackId === t.id && (state === "playing" || state === "loading")) audio.current?.pause();
    else play(t, surface);
  }, [trackId, state, play]);

  const setMuted = useCallback((m: boolean) => { setMutedState(m); if (audio.current) audio.current.muted = m; }, []);

  useEffect(() => () => { audio.current?.pause(); }, []);
  useEffect(() => {
    const onHide = () => { if (document.hidden) audio.current?.pause(); };
    document.addEventListener("visibilitychange", onHide);
    return () => document.removeEventListener("visibilitychange", onHide);
  }, []);

  const value = useMemo(() => ({ state, trackId, progress, muted, unlocked, play, toggle, stop, setMuted }),
    [state, trackId, progress, muted, unlocked, play, toggle, stop, setMuted]);
  return <PlayerCtx.Provider value={value}>{children}</PlayerCtx.Provider>;
}

export function usePlayer() {
  const c = useContext(PlayerCtx);
  if (!c) throw new Error("usePlayer fuori da PlayerProvider");
  return c;
}
