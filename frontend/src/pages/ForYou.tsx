import { useCallback } from "react";
import { Navigate } from "react-router-dom";
import { ButtonLink } from "../components/Pieces";
import { VerticalFeed, type FeedLoader } from "../components/VerticalFeed";
import { useApp } from "../context/AppContext";
import { api, type FeedItem, type FeedPage } from "../lib/api";
import { logoFull, stateImg } from "../lib/assets";
import { prefsQuery, usePrefs } from "../lib/prefs";

const DAILY_KEY = "sonora-daily-shown";

export default function ForYou() {
  const { backend, user } = useApp();
  const prefs = usePrefs();
  const q = prefsQuery(prefs);
  const qKey = JSON.stringify(q);

  // prima pagina + scoperta del giorno insieme: la scoperta è sempre in cima e non sposta i brani
  // mentre si scorre; se è anche tra i brani del feed, il doppione viene tolto dal feed
  const load: FeedLoader = useCallback(async (cursor) => {
    const params = new URLSearchParams({ limit: "10", ...q, ...(cursor ? { cursor } : {}) });
    const today = new Date().toISOString().slice(0, 10);
    let shown: string | null = null;
    try { shown = localStorage.getItem(DAILY_KEY); } catch { /* storage non disponibile */ }
    const wantDaily = !cursor && shown !== today;
    const [page, daily] = await Promise.all([
      api<FeedPage>(`/feed?${params}`),
      wantDaily ? api<{ item: FeedItem | null }>(`/feed/daily?${new URLSearchParams(q)}`).catch(() => ({ item: null })) : Promise.resolve({ item: null }),
    ]);
    let items = page.items;
    if (daily.item) {
      const d = daily.item;
      items = [d, ...items.filter((i) => i.track.id !== d.track.id)];
      try { localStorage.setItem(DAILY_KEY, today); } catch { /* storage non disponibile */ }
    }
    return { items, next_cursor: page.next_cursor, exhausted: page.exhausted };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [qKey]);

  if (!prefs.done) return <Navigate to="/benvenuto" replace />;
  if (backend === "unreachable") return <Empty title="Il feed non è raggiungibile" text="Il server di SONORA non risponde. Riprova tra poco." />;
  if (backend !== "ok") return <Empty title="Un attimo…" text="Sto preparando il tuo feed." />;

  return (
    <VerticalFeed load={load} surface="for_you" reloadKey={`${user?.id ?? "anon"}:${qKey}`}
      top={(
        <div className="pointer-events-none absolute inset-x-0 top-0 z-10 flex items-center px-5 pt-[calc(env(safe-area-inset-top)+0.9rem)] lg:hidden">
          <img src={logoFull} alt="SONORA" className="h-7 w-auto" />
        </div>
      )}
      end={<Empty title="Il catalogo è ancora vuoto" text="Nessun brano importato finora. Chi gestisce SONORA deve avviare l’importazione da Apple Music (vedi README, passo 3)." />} />
  );
}

function Empty({ title, text }: { title: string; text: string }) {
  return (
    <section className="flex min-h-[70dvh] flex-col items-center justify-center px-6 text-center">
      <img src={stateImg("loading_music")} alt="" width={220} height={220} className="h-[220px] w-[220px]" />
      <h1 className="mt-3 text-2xl font-semibold">{title}</h1>
      <p className="mt-2 max-w-sm text-muted">{text}</p>
      <div className="mt-5"><ButtonLink to="/esplora">Esplora generi e mood</ButtonLink></div>
    </section>
  );
}
