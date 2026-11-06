import { useParams } from "react-router-dom";
import { PageTitle } from "../components/Pieces";
import { TrackRow } from "../components/TrackParts";
import { stateImg } from "../lib/assets";
import { findGenre, findMood, genreImg, moodImg } from "../lib/taxonomy";
import { useTrackList } from "../lib/useTrackList";
import NotFound from "./NotFound";

export default function TagPage() {
  const { kind, slug = "" } = useParams();
  const item = kind === "genere" ? findGenre(slug) : kind === "mood" ? findMood(slug) : undefined;
  const list = useTrackList(item ? `/tags/${slug}/tracks?category=${kind === "genere" ? "genre" : "mood"}` : null);
  if (!item) return <NotFound />;
  const img = kind === "genere" ? genreImg(slug) : moodImg(slug);
  return (
    <>
      <div className="relative">
        <img src={img} alt="" width={512} height={512} className="pointer-events-none absolute -right-6 -top-2 h-40 w-40 sm:h-52 sm:w-52" />
        <PageTitle back sub={kind === "genere" ? "Genere" : "Mood"}><span className="relative">{item.label}</span></PageTitle>
      </div>

      {kind === "mood" && list.items.length > 0 && (
        <p className="-mt-3 mb-3 text-sm text-muted">Atmosfera votata da chi ascolta su SONORA.</p>
      )}
      {kind === "mood" && !list.loading && !list.error && list.items.length === 0 ? (
        <section className="flex flex-col items-center py-6 text-center">
          <img src={stateImg("hidden_gems")} alt="" width={200} height={200} className="h-[200px] w-[200px]" />
          <h2 className="mt-2 text-xl font-semibold">Ancora nessun brano {item.label.toLowerCase()}</h2>
          <p className="mt-2 max-w-sm text-muted">Apple Music non dice che atmosfera ha un brano: la decide chi ascolta. Nel feed, tieni premuta una copertina e scegli “Che atmosfera ha?”.</p>
        </section>
      ) : (
        <>
          {list.error && <p role="alert" className="text-danger">{list.error} <button onClick={list.retry} className="font-semibold text-secondary">Riprova</button></p>}
          {!list.loading && !list.error && list.items.length === 0 && (
            <section className="flex flex-col items-center py-6 text-center">
              <img src={stateImg("hidden_gems")} alt="" width={200} height={200} className="h-[200px] w-[200px]" />
              <p className="mt-2 max-w-sm text-muted">Nessun brano {item.label} nel catalogo per ora. Il catalogo si allarga a ogni importazione e a ogni ricerca.</p>
            </section>
          )}
          <ul className="flex flex-col">{list.items.map((t) => <TrackRow key={t.id} t={t} surface={`genre_${slug}`} />)}</ul>
          {list.loading && <p className="py-4 text-center text-sm text-muted">Carico…</p>}
          {list.more && !list.loading && (
            <div className="py-4 text-center"><button onClick={() => void list.more!()} className="rounded-full border border-surface2 px-5 py-2.5 font-semibold hover:bg-surface">Altri brani</button></div>
          )}
          {list.items.length > 0 && kind === "genere" && <p className="mt-4 px-2 text-xs text-muted">Genere indicato da Apple Music.</p>}
        </>
      )}
    </>
  );
}
