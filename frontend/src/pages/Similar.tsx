import { useCallback, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Icon } from "../components/Icon";
import { VerticalFeed, type FeedLoader } from "../components/VerticalFeed";
import { api, type FeedItem, type Track } from "../lib/api";
import { artistNames } from "../lib/format";

/** "Altri brani così": mini feed a partire da un brano. */
export default function Similar() {
  const { id = "" } = useParams();
  const nav = useNavigate();
  const [seed, setSeed] = useState<Track | null>(null);
  const load: FeedLoader = useCallback(async () => {
    const r = await api<{ seed: Track; items: FeedItem[] }>(`/tracks/${id}/similar`);
    setSeed(r.seed);
    return { items: r.items, next_cursor: null, exhausted: true };
  }, [id]);
  return (
    <VerticalFeed load={load} surface="similar" reloadKey={id}
      top={(
        <div className="absolute inset-x-0 top-0 z-10 flex items-center gap-2 px-3 pr-16 pt-[calc(env(safe-area-inset-top)+0.6rem)]">
          <button onClick={() => nav(-1)} aria-label="Indietro" className="grid h-11 w-11 flex-none place-items-center rounded-full bg-bg/50 backdrop-blur">
            <Icon name="chevron_left" size={22} />
          </button>
          <p className="min-w-0 truncate rounded-full bg-bg/50 px-3 py-2 text-sm backdrop-blur">
            {seed ? <>Simili a <strong>{seed.title}</strong> di {artistNames(seed)}</> : "Brani simili"}
          </p>
        </div>
      )}
      end={<p className="grid h-full place-items-center px-8 text-center text-muted">Nessun brano simile nel catalogo per ora.</p>} />
  );
}
