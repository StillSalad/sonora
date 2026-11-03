import { useEffect, useState } from "react";
import { ButtonLink, NotActive, PageTitle } from "../components/Pieces";
import { TrackRow } from "../components/TrackParts";
import { useApp } from "../context/AppContext";
import { api, type Track } from "../lib/api";
import { stateImg } from "../lib/assets";

export default function Collections() {
  const { user, authLoading } = useApp();
  const [likes, setLikes] = useState<Track[] | null>(null);
  useEffect(() => {
    if (!user) { setLikes(null); return; }
    api<{ items: Track[] }>("/me/likes").then((r) => setLikes(r.items)).catch(() => setLikes([]));
  }, [user]);

  return (
    <>
      <PageTitle sub="I brani che ti piacciono e, presto, le tue raccolte.">Raccolte</PageTitle>
      {authLoading ? null : !user ? (
        <section className="flex flex-col items-center py-6 text-center">
          <img src={stateImg("empty_favorites")} alt="" width={220} height={220} className="h-[220px] w-[220px]" />
          <h2 className="mt-2 text-xl font-semibold">Accedi per salvare i brani</h2>
          <p className="mt-2 max-w-sm text-muted">I preferiti e le raccolte sono legati al tuo account.</p>
          <div className="mt-5 flex gap-3">
            <ButtonLink to="/accedi?dopo=/raccolte">Accedi</ButtonLink>
            <ButtonLink to="/registrati" variant="ghost">Crea account</ButtonLink>
          </div>
        </section>
      ) : (
        <>
          <section aria-labelledby="likes">
            <h2 id="likes" className="mb-2 text-lg font-semibold">Mi piace</h2>
            {likes === null ? <p className="text-muted">Carico…</p> : likes.length === 0 ? (
              <div className="flex flex-col items-center py-4 text-center">
                <img src={stateImg("empty_favorites")} alt="" width={180} height={180} className="h-[180px] w-[180px]" />
                <p className="mt-2 max-w-xs text-muted">Tocca il cuore su un brano del feed per ritrovarlo qui.</p>
                <div className="mt-4"><ButtonLink to="/">Vai al feed</ButtonLink></div>
              </div>
            ) : <ul className="flex flex-col">{likes.map((t) => <TrackRow key={t.id} t={t} surface="likes" />)}</ul>}
          </section>
          <section className="mt-6 rounded-tile bg-surface">
            <NotActive feature="collections" image={stateImg("music_dna")} title="Raccolte in arrivo">
              Moodboard con copertina, descrizione e tag, private o pubbliche: arrivano nel prossimo aggiornamento.
            </NotActive>
          </section>
        </>
      )}
    </>
  );
}
