import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Icon } from "../components/Icon";
import { btnGhost, btnPrimary } from "../components/Pieces";
import { useApp } from "../context/AppContext";
import { api, type OnboardingArtist } from "../lib/api";
import { logoFull } from "../lib/assets";
import { getPrefs, savePrefs } from "../lib/prefs";
import { GENRES, genreImg } from "../lib/taxonomy";

const MIN_GENRES = 3;

/** Scelta iniziale: prima i generi, poi gli artisti di quei generi presi dal catalogo. */
export default function Onboarding() {
  const { user, backend } = useApp();
  const nav = useNavigate();
  const [params] = useSearchParams();
  const editing = params.get("modifica") === "1";
  const start = getPrefs();
  const [step, setStep] = useState<1 | 2>(1);
  const [genres, setGenres] = useState<string[]>(editing ? start.genres : []);
  const [artists, setArtists] = useState<{ id: string; name: string }[]>(editing ? start.artists : []);
  const [options, setOptions] = useState<OnboardingArtist[] | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (step !== 2) return;
    setOptions(null);
    api<{ items: OnboardingArtist[] }>(`/onboarding/artists?genres=${genres.join(",")}&limit=36`)
      .then((r) => setOptions(r.items)).catch(() => setOptions([]));
  }, [step, genres]);

  const toggleGenre = (slug: string) => setGenres((g) => (g.includes(slug) ? g.filter((x) => x !== slug) : [...g, slug]));
  const toggleArtist = (a: { id: string; name: string }) =>
    setArtists((x) => (x.some((y) => y.id === a.id) ? x.filter((y) => y.id !== a.id) : [...x, { id: a.id, name: a.name }]));

  async function finish(skipAll = false) {
    setSaving(true);
    await savePrefs(skipAll ? { done: true, genres: [], artists: [] } : { done: true, genres, artists }, user);
    nav(editing ? "/profilo" : "/", { replace: true });
  }

  return (
    <main id="main" className="mx-auto min-h-dvh max-w-2xl px-4 pb-32 pt-[calc(env(safe-area-inset-top)+1.5rem)] sm:px-6 lg:pt-10">
      <div className="flex items-center justify-between">
        <img src={logoFull} alt="SONORA" className="h-7 w-auto" />
        <p className="text-sm text-muted" aria-live="polite">Passo {step} di 2</p>
      </div>

      {step === 1 ? (
        <>
          <h1 className="mt-6 text-[2rem] font-semibold leading-[1.05] tracking-[-0.02em]">Cosa ascolti di solito?</h1>
          <p className="mt-2 text-muted">Scegline almeno {MIN_GENRES}. Il feed partirà da qui, ma ti farà scoprire anche altro.</p>
          <ul className="mt-5 grid grid-cols-3 gap-2.5 sm:grid-cols-4">
            {GENRES.map((g) => {
              const on = genres.includes(g.slug);
              return (
                <li key={g.slug}>
                  <button onClick={() => toggleGenre(g.slug)} aria-pressed={on}
                    className={`relative flex w-full flex-col items-center rounded-tile border-2 bg-surface px-1 pb-2.5 pt-1 transition ${on ? "border-primary bg-primary/10" : "border-transparent hover:bg-surface2"}`}>
                    <img src={genreImg(g.slug)} alt="" width={84} height={84} loading="lazy" className="h-[76px] w-[76px]" />
                    <span className="text-sm font-medium">{g.label}</span>
                    {on && <span className="absolute right-1.5 top-1.5 grid h-6 w-6 place-items-center rounded-full bg-primary text-white"><Icon name="check" size={16} /></span>}
                  </button>
                </li>
              );
            })}
          </ul>
        </>
      ) : (
        <>
          <h1 className="mt-6 text-[2rem] font-semibold leading-[1.05] tracking-[-0.02em]">Qualche artista che ti piace?</h1>
          <p className="mt-2 text-muted">Facoltativo: tocca quelli che conosci e ami. Sono presi dai generi che hai scelto.</p>
          {options === null ? <p className="mt-8 text-center text-muted">Cerco artisti…</p>
            : options.length === 0 ? <p className="mt-8 text-center text-muted">Nessun artista di questi generi nel catalogo per ora. Puoi continuare lo stesso.</p>
            : (
              <ul className="mt-5 grid grid-cols-3 gap-x-3 gap-y-4 sm:grid-cols-4">
                {options.map((a) => {
                  const on = artists.some((x) => x.id === a.id);
                  return (
                    <li key={a.id}>
                      <button onClick={() => toggleArtist(a)} aria-pressed={on} className="flex w-full flex-col items-center text-center">
                        <span className={`relative block aspect-square w-full overflow-hidden rounded-full border-[3px] transition ${on ? "border-primary" : "border-transparent"}`}>
                          {a.artwork_url ? <img src={a.artwork_url} alt="" loading="lazy" className="h-full w-full object-cover" />
                            : <span className="grid h-full w-full place-items-center bg-surface2 font-display text-2xl">{a.name.slice(0, 1)}</span>}
                          {on && <span className="absolute inset-0 grid place-items-center bg-primary/45 text-white"><Icon name="check" size={30} /></span>}
                        </span>
                        <span className="mt-1.5 line-clamp-2 text-sm font-medium leading-tight">{a.name}</span>
                        <span className="text-xs text-muted">{a.genre_label}</span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          <p className="mt-4 text-xs text-muted">Immagini: copertina del brano più noto di ogni artista, da Apple Music.</p>
        </>
      )}

      <div className="fixed inset-x-0 bottom-0 z-30 border-t border-surface2 bg-bg/95 px-4 pb-[calc(env(safe-area-inset-bottom)+0.75rem)] pt-3 backdrop-blur">
        <div className="mx-auto flex max-w-2xl items-center gap-3">
          {step === 1 ? (
            <>
              {!editing && <button onClick={() => void finish(true)} className="px-2 text-sm font-semibold text-muted">Salta</button>}
              <button onClick={() => setStep(2)} disabled={genres.length < MIN_GENRES || backend !== "ok"} className={`${btnPrimary} ml-auto`}>
                {genres.length < MIN_GENRES ? `Scegline ancora ${MIN_GENRES - genres.length}` : `Avanti (${genres.length})`}
              </button>
            </>
          ) : (
            <>
              <button onClick={() => setStep(1)} className={btnGhost}>Indietro</button>
              <button onClick={() => void finish()} disabled={saving} className={`${btnPrimary} ml-auto`}>
                {saving ? "Salvo…" : artists.length ? `Fatto (${artists.length})` : "Fatto"}
              </button>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
