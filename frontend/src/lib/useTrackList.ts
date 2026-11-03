import { useCallback, useEffect, useState } from "react";
import { api, ApiError, type Track } from "./api";

/** Lista paginata a offset (pagine genere). */
export function useTrackList(path: string | null) {
  const [items, setItems] = useState<Track[]>([]);
  const [next, setNext] = useState<number | null>(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (offset: number, reset: boolean) => {
    if (!path) return;
    setLoading(true); setError(null);
    try {
      const sep = path.includes("?") ? "&" : "?";
      const r = await api<{ items: Track[]; next_offset: number | null }>(`${path}${sep}offset=${offset}&limit=20`);
      setItems((p) => (reset ? r.items : [...p, ...r.items]));
      setNext(r.next_offset);
    } catch (e) { setError(e instanceof ApiError ? e.message : "Caricamento non riuscito."); }
    finally { setLoading(false); }
  }, [path]);

  useEffect(() => { setItems([]); setNext(0); void load(0, true); }, [load]);
  return { items, loading, error, more: next !== null && next > 0 ? () => load(next, false) : null, retry: () => load(0, true) };
}
