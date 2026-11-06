import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useApp } from "../context/AppContext";
import { api, ApiError, type MoodSummary, type Track } from "../lib/api";
import { MOODS, moodImg } from "../lib/taxonomy";
import { btnPrimary } from "./Pieces";
import { Sheet } from "./Sheet";

/** "Che atmosfera ha?": fino a 2 mood per brano. Con abbastanza voti diventano tag visibili a tutti. */
export function MoodVoteSheet({ track, open, onClose }: { track: Track; open: boolean; onClose: () => void }) {
  const { user } = useApp();
  const loc = useLocation();
  const [summary, setSummary] = useState<MoodSummary | null>(null);
  const [picked, setPicked] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!open) return;
    setSaved(false); setError(null);
    api<MoodSummary>(`/tracks/${track.id}/moods`).then((s) => { setSummary(s); setPicked(s.mine); }).catch(() => setSummary(null));
  }, [open, track.id]);

  function toggle(slug: string) {
    setPicked((p) => (p.includes(slug) ? p.filter((x) => x !== slug) : p.length >= 2 ? [p[1], slug] : [...p, slug]));
  }
  async function save() {
    setBusy(true); setError(null);
    try { setSummary(await api<MoodSummary>(`/tracks/${track.id}/moods`, { method: "PUT", json: { moods: picked } })); setSaved(true); }
    catch (e) { setError(e instanceof ApiError ? e.message : "Voto non salvato."); }
    finally { setBusy(false); }
  }
  const votes = (slug: string) => summary?.moods.find((m) => m.slug === slug)?.votes ?? 0;

  return (
    <Sheet open={open} title="Che atmosfera ha?" onClose={onClose}>
      <p className="px-2 pb-3 text-sm text-muted">Scegline fino a 2. Quando più persone sono d’accordo, il brano entra in quel mood per tutti.</p>
      <ul className="grid grid-cols-3 gap-2 px-1 sm:grid-cols-4">
        {MOODS.map((m) => {
          const on = picked.includes(m.slug);
          return (
            <li key={m.slug}>
              <button onClick={() => toggle(m.slug)} aria-pressed={on} disabled={!user}
                className={`flex w-full flex-col items-center rounded-2xl border px-1 py-2 text-[13px] transition disabled:opacity-60 ${on ? "border-accent bg-accent/15" : "border-transparent bg-surface2/60 hover:bg-surface2"}`}>
                <img src={moodImg(m.slug)} alt="" width={48} height={48} className="h-12 w-12" />
                <span className="mt-0.5">{m.label}</span>
                {votes(m.slug) > 0 && <span className="text-[11px] text-muted">{votes(m.slug)} {votes(m.slug) === 1 ? "voto" : "voti"}</span>}
              </button>
            </li>
          );
        })}
      </ul>
      <div className="px-2 pt-4">
        {!user ? (
          <p className="text-sm">Per votare serve un account. <Link to={`/accedi?dopo=${encodeURIComponent(loc.pathname)}`} className="font-semibold text-secondary">Accedi</Link></p>
        ) : (
          <>
            {error && <p role="alert" className="mb-2 text-sm text-danger">{error}</p>}
            {saved && <p role="status" className="mb-2 text-sm text-secondary">Grazie, voto salvato.</p>}
            <button onClick={save} disabled={busy} className={`${btnPrimary} w-full`}>{busy ? "Salvo…" : picked.length ? "Salva voto" : "Togli il mio voto"}</button>
          </>
        )}
      </div>
    </Sheet>
  );
}
