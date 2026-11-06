import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import { usePlayer } from "../context/PlayerContext";
import { api, ApiError, type FeedItem } from "../lib/api";
import { Icon } from "./Icon";
import { MoodVoteSheet } from "./MoodVote";
import { ButtonLink } from "./Pieces";
import { Sheet, SheetAction } from "./Sheet";
import { Artwork, ExternalLinks, LikeButton, PlayButton, ShareButton, artistNames, previewNote, useLike } from "./TrackParts";

export type FeedLoader = (cursor: string | null) => Promise<{ items: FeedItem[]; next_cursor: string | null; exhausted: boolean }>;
type Dismissal = { id: string; kind: string; label: string };

/** Feed verticale a schede: una per schermata, scroll a scatto, autoplay dopo il primo tocco,
 *  precaricamento del brano successivo, gesti sulla copertina e menu "Non fa per me". */
export function VerticalFeed({ load, surface, reloadKey, prepend, top, end }: {
  load: FeedLoader; surface: string; reloadKey: string; prepend?: FeedItem[]; top?: ReactNode; end?: ReactNode;
}) {
  const player = usePlayer();
  const [items, setItems] = useState<FeedItem[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [exhausted, setExhausted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [active, setActive] = useState(0);
  const [dismissed, setDismissed] = useState<Record<string, Dismissal>>({});
  const scroller = useRef<HTMLDivElement>(null);
  const busy = useRef(false);

  const fetchPage = useCallback(async (reset: boolean) => {
    if (busy.current) return;
    busy.current = true; setLoading(true); setError(null);
    try {
      const page = await load(reset ? null : cursor);
      setItems((prev) => {
        const base = reset ? [] : prev;
        const known = new Set(base.map((i) => i.track.id));
        return [...base, ...page.items.filter((i) => !known.has(i.track.id))];
      });
      setCursor(page.next_cursor); setExhausted(page.exhausted || !page.next_cursor);
      if (reset) requestAnimationFrame(() => scroller.current?.scrollTo?.({ top: 0 }));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Il feed non si è caricato.");
    } finally { busy.current = false; setLoading(false); }
  }, [load, cursor]);

  useEffect(() => {
    setItems([]); setCursor(null); setExhausted(false); setActive(0); setDismissed({});
    busy.current = false;
    void fetchPage(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reloadKey]);

  // la scoperta del giorno (o altro) in testa, una volta sola
  const all = prepend?.length ? [...prepend.filter((p) => !items.some((i) => i.track.id === p.track.id)), ...items] : items;

  useEffect(() => {
    const root = scroller.current;
    if (!root || typeof IntersectionObserver === "undefined") return;
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) if (e.isIntersecting) setActive(Number((e.target as HTMLElement).dataset.index));
    }, { root, threshold: 0.6 });
    root.querySelectorAll("[data-index]").forEach((n) => io.observe(n));
    return () => io.disconnect();
  }, [all.length]);

  const { unlocked, trackId, play, stop, preload } = player;
  useEffect(() => {
    const t = all[active]?.track;
    if (!t) return;
    if (trackId && trackId !== t.id) stop("skip");
    if (unlocked && t.preview.url && trackId !== t.id && !dismissed[t.id]) play(t, surface);
    // precarica audio del prossimo e copertine dei due successivi
    preload(all[active + 1]?.track);
    for (const n of [1, 2]) { const art = all[active + n]?.track.artwork?.url; if (art) { const i = new Image(); i.src = art; } }
    if (!exhausted && !loading && active >= all.length - 3) void fetchPage(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active, all.length]);

  useEffect(() => () => stop("silent"), [stop]);

  function go(delta: number) {
    const next = scroller.current?.querySelector<HTMLElement>(`[data-index="${active + delta}"]`);
    next?.scrollIntoView?.({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  }

  async function giveFeedback(item: FeedItem, kind: "not_interested" | "less_genre" | "hide_artist") {
    const t = item.track;
    try {
      const r = await api<{ id: string; genre: string | null; artist_id: string | null }>("/feed/feedback", { method: "POST", json: { track_id: t.id, kind } });
      const label = kind === "not_interested" ? "Non lo vedrai più"
        : kind === "hide_artist" ? `Niente più brani di ${artistNames(t)}` : `Meno brani ${r.genre ?? "così"}`;
      if (kind === "less_genre") { flash(label); return; }
      if (trackId === t.id) stop("skip");
      setDismissed((d) => ({ ...d, [t.id]: { id: r.id, kind, label } }));
      if (kind === "hide_artist" && r.artist_id) {
        const idx = all.indexOf(item);
        setItems((prev) => prev.filter((i, k) => i === item || k <= idx || i.track.artists[0]?.id !== r.artist_id));
      }
      setTimeout(() => go(1), 1100);
    } catch (e) { flash(e instanceof ApiError ? e.message : "Non salvato, riprova."); }
  }

  async function undo(trackIdToRestore: string) {
    const d = dismissed[trackIdToRestore];
    if (!d) return;
    await api(`/feed/feedback/${d.id}`, { method: "DELETE" }).catch(() => {});
    setDismissed((x) => { const { [trackIdToRestore]: _, ...rest } = x; return rest; });
  }

  const [toast, setToast] = useState<string | null>(null);
  function flash(msg: string) { setToast(msg); setTimeout(() => setToast(null), 2200); }

  const empty = !loading && !error && all.length === 0;

  return (
    <div className="fixed inset-x-0 bottom-[calc(4.5rem+env(safe-area-inset-bottom))] top-0 lg:bottom-0 lg:left-64">
      {top}
      <button onClick={() => player.setMuted(!player.muted)} aria-label={player.muted ? "Riattiva audio" : "Disattiva audio"}
        className="absolute right-4 top-[calc(env(safe-area-inset-top)+0.6rem)] z-20 grid h-11 w-11 place-items-center rounded-full bg-bg/50 backdrop-blur">
        <Icon name={player.muted ? "volume_off" : "volume"} size={22} />
      </button>
      {toast && <p role="status" className="absolute left-1/2 top-[calc(env(safe-area-inset-top)+4rem)] z-30 -translate-x-1/2 rounded-full bg-surface2 px-4 py-2 text-sm shadow-lg">{toast}</p>}

      <div ref={scroller} tabIndex={0} aria-label="Feed: frecce su e giù per cambiare brano, spazio per ascoltare"
        onKeyDown={(e) => {
          if (e.target !== e.currentTarget) return;
          if (e.key === "ArrowDown" || e.key === "PageDown") { e.preventDefault(); go(1); }
          if (e.key === "ArrowUp" || e.key === "PageUp") { e.preventDefault(); go(-1); }
          if (e.key === " " && all[active]) { e.preventDefault(); player.toggle(all[active].track, surface); }
        }}
        className="h-full snap-y snap-mandatory overflow-y-auto overscroll-contain focus-visible:outline-none">
        {empty && end}
        {all.map((it, i) => (
          <FeedCard key={it.track.id} item={it} index={i} active={i === active} surface={surface}
            dismissed={dismissed[it.track.id]} onFeedback={(k) => giveFeedback(it, k)} onUndo={() => undo(it.track.id)} />
        ))}
        {exhausted && all.length > 0 ? (
          <section className="grid h-full snap-start place-items-center px-6 text-center">
            <div className="max-w-xs"><p className="font-display text-xl font-semibold">Hai visto tutto per ora</p>
              <p className="mt-2 text-muted">Il catalogo si aggiorna ogni giorno. Intanto cerca qualcosa o esplora un genere.</p>
              <div className="mt-5"><ButtonLink to="/esplora">Esplora</ButtonLink></div></div>
          </section>
        ) : (
          /* non è un punto di aggancio: i nuovi brani si inseriscono prima senza far saltare lo scroll */
          <div className="px-6 py-10 text-center">
            {loading ? <p className="text-muted">Carico altri brani…</p>
              : error ? <><p className="mb-3">{error}</p><button onClick={() => void fetchPage(all.length === 0)} className="font-semibold text-secondary">Riprova</button></>
              : null}
          </div>
        )}
      </div>
    </div>
  );
}

const TAP_MS = 280, HOLD_MS = 480;

function FeedCard({ item, index, active, surface, dismissed, onFeedback, onUndo }: {
  item: FeedItem; index: number; active: boolean; surface: string; dismissed?: Dismissal;
  onFeedback: (k: "not_interested" | "less_genre" | "hide_artist") => void; onUndo: () => void;
}) {
  const t = item.track;
  const player = usePlayer();
  const nav = useNavigate();
  const like = useLike(t, surface);
  const [menu, setMenu] = useState(false);
  const [moods, setMoods] = useState(false);
  const [burst, setBurst] = useState(0);
  const g = useRef({ down: 0, x: 0, y: 0, hold: 0 as unknown as ReturnType<typeof setTimeout>, held: false, lastTap: 0,
    single: 0 as unknown as ReturnType<typeof setTimeout> });
  const note = previewNote(t);
  const highlight = item.slot === "discovery" || item.slot === "daily";
  const first = t.artists[0];
  const genre = t.tags.find((x) => x.category === "genre");
  const moodTags = t.tags.filter((x) => x.category === "mood");

  // gesti sulla copertina: tocco = play/pausa, doppio tocco = Mi piace, tieni premuto = menu
  function onDown(e: React.PointerEvent) {
    const s = g.current;
    s.down = Date.now(); s.x = e.clientX; s.y = e.clientY; s.held = false;
    clearTimeout(s.hold);
    s.hold = setTimeout(() => { s.held = true; navigator.vibrate?.(12); setMenu(true); }, HOLD_MS);
  }
  function onMove(e: React.PointerEvent) {
    const s = g.current;
    if (Math.abs(e.clientX - s.x) > 10 || Math.abs(e.clientY - s.y) > 10) clearTimeout(s.hold);
  }
  function onUp(e: React.PointerEvent) {
    const s = g.current;
    clearTimeout(s.hold);
    if (s.held || Math.abs(e.clientX - s.x) > 10 || Math.abs(e.clientY - s.y) > 10) return;
    const now = Date.now();
    if (now - s.lastTap < TAP_MS) {
      clearTimeout(s.single); s.lastTap = 0;
      setBurst((b) => b + 1);
      if (like.loggedIn) void like.like(); else like.toggle();
      return;
    }
    s.lastTap = now;
    s.single = setTimeout(() => { if (t.preview.url) player.toggle(t, surface); }, TAP_MS);
  }

  if (dismissed)
    return (
      <section data-index={index} className="grid h-full snap-start snap-always place-items-center px-8 text-center">
        <div role="status">
          <Icon name="check" size={36} className="mx-auto text-secondary" />
          <p className="mt-3 font-display text-xl font-semibold">{dismissed.label}</p>
          <p className="mt-1 text-sm text-muted">Il feed ne terrà conto da subito.</p>
          <button onClick={onUndo} className="mt-5 rounded-full border border-surface2 px-5 py-2.5 font-semibold hover:bg-surface">Annulla</button>
        </div>
      </section>
    );

  return (
    <section data-index={index} aria-roledescription="brano" aria-label={`${t.title} di ${artistNames(t)}`}
      className="relative flex h-full snap-start snap-always flex-col items-center justify-center overflow-hidden px-6 pb-5 pt-16">
      {t.artwork && <img src={t.artwork.url} alt="" aria-hidden="true" className="pointer-events-none absolute inset-0 h-full w-full scale-125 object-cover opacity-30 blur-3xl" />}
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 bg-gradient-to-b from-bg/40 via-bg/70 to-bg" />

      <div className="relative flex w-full max-w-[400px] flex-col">
        <div className="gesture-surface relative" onPointerDown={onDown} onPointerMove={onMove} onPointerUp={onUp}
          onPointerCancel={() => clearTimeout(g.current.hold)} onContextMenu={(e) => e.preventDefault()}>
          <Artwork t={t} size={600} className={`w-full rounded-[1.6rem] shadow-2xl shadow-black/50 transition-transform duration-500 ${active ? "scale-100" : "scale-[0.97]"}`} />
          {burst > 0 && (
            <span key={burst} aria-hidden="true" className="heart-burst pointer-events-none absolute inset-0 grid place-items-center text-white drop-shadow-[0_6px_20px_rgba(232,121,249,.7)]">
              <Icon name="heart_filled" size={120} />
            </span>
          )}
          {item.slot === "daily" && (
            <span className="absolute left-3 top-3 rounded-full bg-accent px-3 py-1 text-xs font-bold text-white shadow-lg">Scoperta del giorno</span>
          )}
        </div>

        <div className="mt-4 flex items-start gap-2">
          <p className={`inline-flex min-w-0 items-center gap-1.5 rounded-full px-3 py-1 text-[13px] font-medium ${highlight ? "bg-accent/15 text-accent" : "bg-secondary/15 text-secondary"}`}>
            <Icon name={highlight ? "hidden_gems" : "trending"} size={15} />
            <span className="truncate">{item.explanation}</span>
          </p>
          <button onClick={() => setMenu(true)} aria-label="Altre azioni" className="-mr-2 -mt-1 ml-auto grid h-10 w-10 flex-none place-items-center rounded-full text-muted hover:bg-surface2 hover:text-ink">
            <Icon name="more" size={22} />
          </button>
        </div>

        <h2 className="mt-2 line-clamp-2 text-[1.75rem] font-semibold leading-[1.08] tracking-[-0.02em]">{t.title}</h2>
        <p className="mt-1 truncate text-[17px]">{first ? <Link to={`/artista/${first.id}`} className="hover:underline">{artistNames(t)}</Link> : null}</p>
        <p className="truncate text-sm text-muted">{t.album?.title}{t.release_year ? `, ${t.release_year}` : ""}</p>

        <ul className="mt-3 flex flex-wrap gap-1.5">
          {genre && <li><Link to={`/esplora/genere/${genre.slug}`} className="rounded-full bg-surface2/80 px-2.5 py-1 text-xs hover:bg-surface2">#{genre.label}</Link></li>}
          {moodTags.map((m) => (
            <li key={m.slug}><Link to={`/esplora/mood/${m.slug}`} title="Atmosfera votata dalla community" className="rounded-full bg-accent/15 px-2.5 py-1 text-xs text-accent hover:bg-accent/25">{m.label}</Link></li>
          ))}
          <li><button onClick={() => nav(`/simili/${t.id}`)} className="inline-flex items-center gap-1 rounded-full bg-surface2/80 px-2.5 py-1 text-xs hover:bg-surface2">
            <Icon name="random" size={13} /> Altri brani così</button></li>
        </ul>

        <div className="mt-4 flex items-center gap-2">
          <PlayButton t={t} surface={surface} size={60} />
          <div className="flex flex-none items-center">
            <LikeButton liked={like.liked} onToggle={() => void like.toggle()} />
            <ShareButton t={t} surface={surface} />
          </div>
          <div className="ml-auto flex min-w-0 justify-end"><ExternalLinks t={t} surface={surface} /></div>
        </div>
        <div className="mt-2.5 min-h-[1.25rem] text-xs text-muted">
          {note ?? (t.artwork ? `Anteprima di 30 secondi e copertina da ${t.artwork.attribution}` : null)}
          {t.demo && <span className="ml-1 text-accent">Dato demo fittizio.</span>}
        </div>
      </div>

      <Sheet open={menu} title={t.title} onClose={() => setMenu(false)}>
        <SheetAction icon="close" label="Non mi interessa" hint="Non vedrai più questo brano" onClick={() => { setMenu(false); onFeedback("not_interested"); }} />
        {genre && <SheetAction icon="filter" label={`Meno brani ${genre.label}`} hint="Il genere compare meno spesso" onClick={() => { setMenu(false); onFeedback("less_genre"); }} />}
        {first && <SheetAction icon="artist" label={`Nascondi ${first.name}`} hint="Nessun brano di questo artista nel feed" onClick={() => { setMenu(false); onFeedback("hide_artist"); }} />}
        <div className="my-1 h-px bg-surface2" />
        <SheetAction icon="random" label="Altri brani così" onClick={() => { setMenu(false); nav(`/simili/${t.id}`); }} />
        <SheetAction icon="hidden_gems" label="Che atmosfera ha?" hint="Vota il mood del brano" onClick={() => { setMenu(false); setMoods(true); }} />
      </Sheet>
      <MoodVoteSheet track={t} open={moods} onClose={() => setMoods(false)} />
    </section>
  );
}
