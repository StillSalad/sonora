import { useSyncExternalStore } from "react";
import { api, type User } from "./api";

/** Gusti scelti all'inizio. Salvati sul dispositivo (valgono anche senza account) e, con un account,
 *  anche sul server, così si ritrovano su un altro telefono. */
export type Prefs = { done: boolean; genres: string[]; artists: { id: string; name: string }[] };

const KEY = "sonora-prefs";
const EMPTY: Prefs = { done: false, genres: [], artists: [] };
let current: Prefs = read();
const listeners = new Set<() => void>();

function read(): Prefs {
  try {
    const v = JSON.parse(localStorage.getItem(KEY) || "null");
    if (v && Array.isArray(v.genres) && Array.isArray(v.artists)) return { done: !!v.done, genres: v.genres, artists: v.artists };
  } catch { /* storage non disponibile */ }
  return EMPTY;
}

export function getPrefs(): Prefs { return current; }

export function setPrefs(p: Prefs) {
  current = p;
  try { localStorage.setItem(KEY, JSON.stringify(p)); } catch { /* storage non disponibile */ }
  listeners.forEach((l) => l());
}

export function usePrefs(): Prefs {
  return useSyncExternalStore((l) => { listeners.add(l); return () => listeners.delete(l); }, getPrefs, getPrefs);
}

/** Parametri del feed: g=generi, a=artisti. */
export function prefsQuery(p: Prefs = current): Record<string, string> {
  const q: Record<string, string> = {};
  if (p.genres.length) q.g = p.genres.join(",");
  if (p.artists.length) q.a = p.artists.map((a) => a.id).join(",");
  return q;
}

export async function savePrefs(p: Prefs, user: User | null) {
  setPrefs(p);
  if (user) await api("/me/preferences", { method: "PUT", json: { genres: p.genres, artists: p.artists.map((a) => a.id) } }).catch(() => {});
}

/** All'accesso: se il dispositivo non ha ancora scelto nulla prende le scelte dell'account, altrimenti le salva sull'account. */
export async function syncPrefs(user: User) {
  try {
    const server = await api<{ genres: string[]; artists: { id: string; name: string }[] }>("/me/preferences");
    const local = getPrefs();
    if (!local.done && (server.genres.length || server.artists.length)) setPrefs({ done: true, ...server });
    else if (local.done && !server.genres.length && !server.artists.length && (local.genres.length || local.artists.length))
      await savePrefs(local, user);
  } catch { /* offline: riproverà al prossimo accesso */ }
}
