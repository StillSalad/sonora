import { Link } from "react-router-dom";
import { PageTitle } from "../components/Pieces";
import { GENRES, MOODS, genreImg, moodImg } from "../lib/taxonomy";

export default function Explore() {
  return (
    <>
      <PageTitle sub="Parti da come ti senti o da un genere.">Esplora</PageTitle>

      <section aria-labelledby="moods">
        <h2 id="moods" className="mb-3 text-lg font-semibold">Mood</h2>
        <ul className="scroll-x -mx-4 flex gap-3 px-4 pb-2 sm:-mx-6 sm:px-6 lg:mx-0 lg:flex-wrap lg:px-0">
          {MOODS.map((m) => (
            <li key={m.slug} className="w-[92px] flex-none snap-start">
              <Link to={`/esplora/mood/${m.slug}`} className="group flex flex-col items-center gap-1.5">
                <span className="grid h-[92px] w-[92px] place-items-center rounded-full bg-surface transition group-hover:bg-surface2">
                  <img src={moodImg(m.slug)} alt="" width={84} height={84} loading="lazy" className="h-[84px] w-[84px]" />
                </span>
                <span className="text-sm">{m.label}</span>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="genres" className="mt-8">
        <h2 id="genres" className="mb-3 text-lg font-semibold">Generi</h2>
        <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {GENRES.map((g) => (
            <li key={g.slug}>
              <Link to={`/esplora/genere/${g.slug}`}
                className="group relative block aspect-[5/4] overflow-hidden rounded-tile bg-surface transition hover:bg-surface2">
                <img src={genreImg(g.slug)} alt="" width={512} height={512} loading="lazy"
                  className="absolute -bottom-[14%] -right-[16%] h-[92%] w-auto transition-transform duration-300 group-hover:-translate-y-1" />
                <span className="absolute left-4 top-3.5 font-display text-[1.15rem] font-semibold leading-tight">{g.label}</span>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
