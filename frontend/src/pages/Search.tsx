import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Icon } from "../components/Icon";
import { PageTitle, field } from "../components/Pieces";
import { TrackRow } from "../components/TrackParts";
import { useApp } from "../context/AppContext";
import { api, ApiError, sendEvent, type Track } from "../lib/api";
import { stateImg } from "../lib/assets";

const LIVE_NOTE: Record<string, string | null> = {
  ok: null, cached: null, skipped: null, disabled: null,
  unavailable: "Apple Music non risponde: vedi solo i brani già nel catalogo di SONORA.",
};

export default function Search() {
  const { backend } = useApp();
  const [params, setParams] = useSearchParams();
  const [q, setQ] = useState(params.get("q") ?? "");
  const [items, setItems] = useState<Track[] | null>(null);
  const [live, setLive] = useState<string>("skipped");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const reqId = useRef(0);

  useEffect(() => {
    const term = q.trim();
    if (term.length < 2) { setItems(null); setError(null); return; }
    const id = ++reqId.current;
    const timer = setTimeout(async () => {
      setLoading(true); setError(null);
      setParams(term ? { q: term } : {}, { replace: true });
      try {
        const r = await api<{ items: Track[]; live: string }>(`/search?${new URLSearchParams({ q: term, limit: "25" })}`);
        if (id === reqId.current) { setItems(r.items); setLive(r.live); }
      } catch (e) {
        if (id === reqId.current) setError(e instanceof ApiError ? e.message : "Ricerca non riuscita.");
      } finally { if (id === reqId.current) setLoading(false); }
    }, 350);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q]);

  return (
    <>
      <PageTitle>Cerca</PageTitle>
      <form role="search" onSubmit={(e) => e.preventDefault()} className="relative">
        <label htmlFor="q" className="sr-only">Cerca brani, artisti o album</label>
        <Icon name="search" size={20} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-muted" />
        <input id="q" type="search" value={q} onChange={(e) => setQ(e.target.value)} disabled={backend !== "ok"}
          autoComplete="off" placeholder="Brani, artisti, album" className={`${field} pl-12 disabled:opacity-60`} />
      </form>

      <div aria-live="polite" className="mt-4">
        {loading && <p className="px-2 text-sm text-muted">Cerco…</p>}
        {error && <p role="alert" className="px-2 text-sm text-danger">{error}</p>}
        {LIVE_NOTE[live] && items && <p className="px-2 pb-2 text-sm text-muted">{LIVE_NOTE[live]}</p>}
        {items && items.length === 0 && !loading && (
          <p className="px-2 py-6 text-center text-muted">Nessun risultato per “{q.trim()}”. Prova con il nome dell’artista.</p>
        )}
      </div>

      {items && items.length > 0 ? (
        <ul className="flex flex-col" onClick={(e) => {
          const li = (e.target as HTMLElement).closest("li");
          const idx = li ? Array.from(li.parentElement!.children).indexOf(li) : -1;
          if (idx >= 0 && items[idx]) sendEvent(items[idx].id, "search_click", { source_surface: "search" });
        }}>
          {items.map((t) => <TrackRow key={t.id} t={t} surface="search" />)}
        </ul>
      ) : !items && (
        <section className="flex flex-col items-center py-8 text-center">
          <img src={stateImg("hidden_gems")} alt="" width={200} height={200} className="h-[200px] w-[200px]" />
          <p className="mt-2 max-w-xs text-muted">Scrivi almeno due lettere. Se un brano non è ancora nel catalogo, SONORA lo cerca su Apple Music.</p>
        </section>
      )}
      <p className="mt-6 px-2 text-xs text-muted">Risultati, copertine e anteprime da Apple Music.</p>
    </>
  );
}
