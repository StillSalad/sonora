import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext";
import { usePlayer } from "../context/PlayerContext";
import { api, sendEvent, type Track } from "../lib/api";
import { logoFull } from "../lib/assets";
import { Icon } from "./Icon";

export const artistNames = (t: Track) => t.artists.filter((a) => a.role === "primary").map((a) => a.name).join(", ") || t.artists[0]?.name;

export function previewNote(t: Track): string | null {
  switch (t.preview.status) {
    case "AVAILABLE": return t.preview.url ? null : "Anteprima non disponibile qui";
    case "EXTERNAL_ONLY": return "Anteprima non disponibile: ascoltalo sul servizio";
    case "RIGHTS_PENDING": return "Anteprima in verifica";
    default: return "Anteprima non disponibile";
  }
}

export function Artwork({ t, size, className = "" }: { t: Track; size: number; className?: string }) {
  if (t.artwork)
    return <img src={t.artwork.url} alt={`Copertina di ${t.album?.title ?? t.title}`} width={size} height={size} loading="lazy"
      className={`aspect-square bg-surface2 object-cover ${className}`} />;
  return (
    <div role="img" aria-label="Copertina non disponibile" className={`grid aspect-square place-items-center bg-surface2 ${className}`}>
      <img src={logoFull} alt="" className="w-1/2 opacity-20" />
    </div>
  );
}

/** Pulsante play con anello di avanzamento (30 s). */
export function PlayButton({ t, surface, size = 64 }: { t: Track; surface: string; size?: number }) {
  const { state, trackId, progress, toggle } = usePlayer();
  const mine = trackId === t.id;
  const playing = mine && (state === "playing" || state === "loading");
  const r = size / 2 - 3, c = 2 * Math.PI * r;
  const disabled = !t.preview.url;
  return (
    <button onClick={() => toggle(t, surface)} disabled={disabled}
      aria-label={disabled ? "Anteprima non disponibile" : playing ? `Pausa ${t.title}` : `Ascolta l’anteprima di ${t.title}`}
      className="relative grid flex-none place-items-center rounded-full bg-primary text-white transition hover:brightness-110 disabled:bg-surface2 disabled:text-muted"
      style={{ width: size, height: size }}>
      {mine && (
        <svg aria-hidden="true" className="absolute inset-0 -rotate-90" width={size} height={size}>
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgb(255 255 255 / .25)" strokeWidth="3" />
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgb(var(--secondary))" strokeWidth="3"
            strokeDasharray={c} strokeDashoffset={c * (1 - progress)} strokeLinecap="round" />
        </svg>
      )}
      {mine && state === "loading" ? <span className="h-5 w-5 animate-spin rounded-full border-2 border-white/40 border-t-white" />
        : <Icon name={playing ? "pause" : "play"} size={size * 0.42} />}
    </button>
  );
}

export function LikeButton({ t, surface }: { t: Track; surface: string }) {
  const { user } = useApp();
  const nav = useNavigate();
  const loc = useLocation();
  const [liked, setLiked] = useState(t.liked);
  const [busy, setBusy] = useState(false);
  async function click() {
    if (!user) { nav(`/accedi?dopo=${encodeURIComponent(loc.pathname)}`); return; }
    setBusy(true);
    const next = !liked;
    setLiked(next);
    try {
      await api(`/tracks/${t.id}/like`, { method: next ? "POST" : "DELETE" });
      sendEvent(t.id, next ? "like" : "unlike", { source_surface: surface });
    } catch { setLiked(!next); } finally { setBusy(false); }
  }
  return (
    <button onClick={click} disabled={busy} aria-pressed={liked} aria-label={liked ? "Togli da Mi piace" : "Mi piace"}
      className={`grid h-12 w-12 place-items-center rounded-full transition hover:bg-surface2 ${liked ? "text-accent" : ""}`}>
      <Icon name={liked ? "heart_filled" : "heart"} size={26} />
    </button>
  );
}

export function ShareButton({ t, surface }: { t: Track; surface: string }) {
  const [copied, setCopied] = useState(false);
  const url = t.links[0]?.url;
  if (!url) return null;
  async function share() {
    const text = `${t.title} di ${artistNames(t)}`;
    try {
      if (navigator.share) await navigator.share({ title: t.title, text, url });
      else { await navigator.clipboard.writeText(`${text} ${url}`); setCopied(true); setTimeout(() => setCopied(false), 1800); }
      sendEvent(t.id, "share", { source_surface: surface });
    } catch { /* condivisione annullata */ }
  }
  return (
    <button onClick={share} aria-label="Condividi" className="relative grid h-12 w-12 place-items-center rounded-full hover:bg-surface2">
      <Icon name="share" size={24} />
      {copied && <span role="status" className="absolute -top-8 whitespace-nowrap rounded-lg bg-surface2 px-2 py-1 text-xs">Link copiato</span>}
    </button>
  );
}

export function ExternalLinks({ t, surface, compact = false }: { t: Track; surface: string; compact?: boolean }) {
  return (
    <>
      {t.links.map((l) => (
        <a key={l.provider} href={l.url} target="_blank" rel="noopener noreferrer"
          onClick={() => sendEvent(t.id, "external_open", { source_surface: surface })}
          className={compact ? "grid h-10 w-10 place-items-center rounded-full text-muted hover:bg-surface2 hover:text-ink"
            : "inline-flex items-center gap-2 whitespace-nowrap rounded-full border border-surface2 px-4 py-2.5 text-sm font-semibold hover:bg-surface2"}
          aria-label={compact ? l.label : undefined}>
          <Icon name="external_link" size={compact ? 20 : 18} />
          {!compact && l.label}
        </a>
      ))}
    </>
  );
}

/** Riga compatta per ricerca, pagine genere, artista e preferiti. */
export function TrackRow({ t, surface }: { t: Track; surface: string }) {
  const note = previewNote(t);
  const first = t.artists[0];
  return (
    <li className="flex items-center gap-3 rounded-2xl px-2 py-2 hover:bg-surface">
      <Artwork t={t} size={56} className="h-14 w-14 flex-none rounded-xl" />
      <div className="min-w-0 flex-1">
        <p className="truncate font-semibold">{t.title}{t.explicit && <span className="ml-1.5 rounded bg-surface2 px-1 text-[10px] font-bold text-muted" aria-label="esplicito">E</span>}</p>
        <p className="truncate text-sm text-muted">
          {first ? <Link to={`/artista/${first.id}`} className="hover:text-ink">{artistNames(t)}</Link> : null}
          {t.release_year ? `, ${t.release_year}` : ""}
        </p>
        {note && <p className="truncate text-xs text-muted/80">{note}</p>}
        {t.demo && <p className="text-xs text-accent">Dato demo fittizio</p>}
      </div>
      <ExternalLinks t={t} surface={surface} compact />
      <PlayButton t={t} surface={surface} size={44} />
    </li>
  );
}
