import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Icon } from "../components/Icon";
import { ButtonLink } from "../components/Pieces";
import { Artwork, ExternalLinks, LikeButton, PlayButton, ShareButton, artistNames, previewNote } from "../components/TrackParts";
import { useApp } from "../context/AppContext";
import { usePlayer } from "../context/PlayerContext";
import { api, ApiError, type FeedItem, type FeedPage } from "../lib/api";
import { logoFull, stateImg } from "../lib/assets";

const SURFACE = "for_you";

export default function ForYou() {
  const { backend, user } = useApp();
  const player = usePlayer();
  const [items, setItems] = useState<FeedItem[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [exhausted, setExhausted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [active, setActive] = useState(0);
  const scroller = useRef<HTMLDivElement>(null);
  const loadingRef = useRef(false);

  const load = useCallback(async (reset = false) => {
    if (loadingRef.current) return;
    loadingRef.current = true; setLoading(true); setError(null);
    try {
      const qs = new URLSearchParams({ limit: "10" });
      if (!reset && cursor) qs.set("cursor", cursor);
      const page = await api<FeedPage>(`/feed?${qs}`);
      setItems((prev) => (reset ? page.items : [...prev, ...page.items]));
      setCursor(page.next_cursor);
      setExhausted(page.exhausted);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Il feed non si è caricato.");
    } finally { loadingRef.current = false; setLoading(false); }
  }, [cursor]);

  // primo caricamento e nuovo feed quando cambia l'utente (i gusti cambiano le spiegazioni)
  useEffect(() => {
    if (backend !== "ok") return;
    setItems([]); setCursor(null); setExhausted(false); setActive(0);
    loadingRef.current = false;
    void (async () => {
      loadingRef.current = true; setLoading(true);
      try {
        const page = await api<FeedPage>("/feed?limit=10");
        setItems(page.items); setCursor(page.next_cursor); setExhausted(page.exhausted);
        requestAnimationFrame(() => scroller.current?.scrollTo({ top: 0 }));
      } catch (e) { setError(e instanceof ApiError ? e.message : "Il feed non si è caricato."); }
      finally { loadingRef.current = false; setLoading(false); }
    })();
  }, [backend, user?.id]);

  // scheda attiva = quella visibile per almeno il 60%
  useEffect(() => {
    const root = scroller.current;
    if (!root || typeof IntersectionObserver === "undefined") return;
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) if (e.isIntersecting) setActive(Number((e.target as HTMLElement).dataset.index));
    }, { root, threshold: 0.6 });
    root.querySelectorAll("[data-index]").forEach((n) => io.observe(n));
    return () => io.disconnect();
  }, [items.length]);

  // cambio scheda: l'audio segue solo dopo il primo tocco su play
  const { unlocked, trackId, play, stop } = player;
  useEffect(() => {
    const t = items[active]?.track;
    if (!t) return;
    if (trackId && trackId !== t.id) stop("skip");
    if (unlocked && t.preview.url && trackId !== t.id) play(t, SURFACE);
    if (!exhausted && active >= items.length - 3) void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active]);

  useEffect(() => () => stop("silent"), [stop]);

  function go(delta: number) {
    const next = scroller.current?.querySelector<HTMLElement>(`[data-index="${active + delta}"]`);
    next?.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  }

  if (backend === "unreachable") return <Empty title="Il feed non è raggiungibile" text="Il server di SONORA non risponde. Riprova tra poco." />;
  if (!loading && !error && items.length === 0 && backend === "ok")
    return <Empty title="Il catalogo è ancora vuoto"
      text="Nessun brano importato finora. Chi gestisce SONORA deve avviare l’importazione da Apple Music (vedi README, passo 3)." />;

  return (
    <div className="fixed inset-x-0 bottom-[calc(4.5rem+env(safe-area-inset-bottom))] top-0 lg:bottom-0 lg:left-64">
      <div className="pointer-events-none absolute inset-x-0 top-0 z-10 flex items-center justify-between px-5 pt-[calc(env(safe-area-inset-top)+0.9rem)] lg:hidden">
        <img src={logoFull} alt="SONORA" className="h-7 w-auto" />
      </div>
      <button onClick={() => player.setMuted(!player.muted)} aria-label={player.muted ? "Riattiva audio" : "Disattiva audio"}
        className="absolute right-4 top-[calc(env(safe-area-inset-top)+0.6rem)] z-10 grid h-11 w-11 place-items-center rounded-full bg-bg/50 backdrop-blur">
        <Icon name={player.muted ? "volume_off" : "volume"} size={22} />
      </button>

      <div ref={scroller} tabIndex={0} aria-label="Feed Per te: usa le frecce su e giù per cambiare brano, spazio per ascoltare"
        onKeyDown={(e) => {
          if (e.key === "ArrowDown" || e.key === "PageDown") { e.preventDefault(); go(1); }
          if (e.key === "ArrowUp" || e.key === "PageUp") { e.preventDefault(); go(-1); }
          if (e.key === " " && items[active]) { e.preventDefault(); player.toggle(items[active].track, SURFACE); }
        }}
        className="h-full snap-y snap-mandatory overflow-y-auto overscroll-contain focus-visible:outline-none">
        {items.map((it, i) => <FeedCard key={it.track.id} item={it} index={i} active={i === active} />)}
        {exhausted && items.length > 0 ? (
          <section className="grid h-full snap-start place-items-center px-6 text-center">
            <div className="max-w-xs"><p className="font-display text-xl font-semibold">Hai visto tutto per ora</p>
              <p className="mt-2 text-muted">Il catalogo si aggiorna ogni giorno. Intanto cerca qualcosa o esplora un genere.</p>
              <div className="mt-5"><ButtonLink to="/esplora">Esplora</ButtonLink></div></div>
          </section>
        ) : (
          /* non è un punto di aggancio: i nuovi brani si inseriscono prima senza far saltare lo scroll */
          <div className="px-6 py-10 text-center">
            {loading ? <p className="text-muted">Carico altri brani…</p>
              : error ? <><p className="mb-3">{error}</p><button onClick={() => void load()} className="font-semibold text-secondary">Riprova</button></>
              : null}
          </div>
        )}
      </div>
    </div>
  );
}

function FeedCard({ item, index, active }: { item: FeedItem; index: number; active: boolean }) {
  const t = item.track;
  const note = previewNote(t);
  const discovery = item.slot === "discovery";
  const first = t.artists[0];
  return (
    <section data-index={index} aria-roledescription="brano" aria-label={`${t.title} di ${artistNames(t)}`}
      className="relative flex h-full snap-start snap-always flex-col items-center justify-center overflow-hidden px-6 pb-6 pt-16">
      {t.artwork && (
        <img src={t.artwork.url} alt="" aria-hidden="true"
          className="pointer-events-none absolute inset-0 h-full w-full scale-125 object-cover opacity-30 blur-3xl" />
      )}
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 bg-gradient-to-b from-bg/40 via-bg/70 to-bg" />

      <div className="relative flex w-full max-w-[400px] flex-col">
        <Artwork t={t} size={600} className={`w-full rounded-[1.6rem] shadow-2xl shadow-black/50 transition-transform duration-500 ${active ? "scale-100" : "scale-[0.97]"}`} />

        <p className={`mt-5 inline-flex max-w-full items-center gap-1.5 self-start rounded-full px-3 py-1 text-[13px] font-medium ${discovery ? "bg-accent/15 text-accent" : "bg-secondary/15 text-secondary"}`}>
          <Icon name={discovery ? "hidden_gems" : "trending"} size={15} />
          <span className="truncate">{item.explanation}</span>
        </p>

        <h2 className="mt-3 line-clamp-2 text-[1.75rem] font-semibold leading-[1.08] tracking-[-0.02em]">{t.title}</h2>
        <p className="mt-1 truncate text-[17px]">
          {first ? <Link to={`/artista/${first.id}`} className="hover:underline">{artistNames(t)}</Link> : null}
        </p>
        <p className="truncate text-sm text-muted">
          {t.album?.title}{t.release_year ? `, ${t.release_year}` : ""}
        </p>
        {t.tags.length > 0 && (
          <ul className="mt-3 flex flex-wrap gap-1.5">
            {t.tags.filter((g) => g.category === "genre").map((g) => (
              <li key={g.slug}><Link to={`/esplora/genere/${g.slug}`} className="rounded-full bg-surface2/80 px-2.5 py-1 text-xs hover:bg-surface2">#{g.label}</Link></li>
            ))}
          </ul>
        )}

        <div className="mt-5 flex items-center gap-2">
          <PlayButton t={t} surface={SURFACE} size={64} />
          <div className="ml-1 flex flex-1 items-center">
            <LikeButton t={t} surface={SURFACE} />
            <ShareButton t={t} surface={SURFACE} />
          </div>
          <ExternalLinks t={t} surface={SURFACE} />
        </div>
        <div className="mt-3 min-h-[1.25rem] text-xs text-muted">
          {note ?? (t.artwork ? `Anteprima di 30 secondi e copertina da ${t.artwork.attribution}` : null)}
          {t.demo && <span className="ml-1 text-accent">Dato demo fittizio.</span>}
        </div>
      </div>
    </section>
  );
}

function Empty({ title, text }: { title: string; text: string }) {
  return (
    <section className="flex min-h-[70dvh] flex-col items-center justify-center text-center">
      <img src={stateImg("loading_music")} alt="" width={220} height={220} className="h-[220px] w-[220px]" />
      <h1 className="mt-3 text-2xl font-semibold">{title}</h1>
      <p className="mt-2 max-w-sm text-muted">{text}</p>
      <div className="mt-5"><ButtonLink to="/esplora">Esplora generi e mood</ButtonLink></div>
    </section>
  );
}
