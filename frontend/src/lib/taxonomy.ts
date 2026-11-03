// Etichette italiane per generi e mood. Le illustrazioni sono in /public/assets.
export const GENRES: { slug: string; label: string }[] = [
  { slug: "pop", label: "Pop" }, { slug: "rap", label: "Rap" }, { slug: "indie", label: "Indie" },
  { slug: "rock", label: "Rock" }, { slug: "electronic", label: "Elettronica" }, { slug: "rnb", label: "R&B" },
  { slug: "latin", label: "Latina" }, { slug: "jazz", label: "Jazz" }, { slug: "classical", label: "Classica" },
  { slug: "trap", label: "Trap" }, { slug: "house", label: "House" }, { slug: "techno", label: "Techno" },
  { slug: "soul", label: "Soul" }, { slug: "funk", label: "Funk" }, { slug: "disco", label: "Disco" },
  { slug: "kpop", label: "K-pop" }, { slug: "afrobeat", label: "Afrobeat" }, { slug: "reggae", label: "Reggae" },
  { slug: "metal", label: "Metal" }, { slug: "punk", label: "Punk" }, { slug: "drill", label: "Drill" },
  { slug: "blues", label: "Blues" }, { slug: "folk", label: "Folk" }, { slug: "country", label: "Country" },
  { slug: "ambient", label: "Ambient" }, { slug: "gospel", label: "Gospel" }, { slug: "soundtrack", label: "Colonne sonore" },
];

export const MOODS: { slug: string; label: string }[] = [
  { slug: "energy", label: "Energia" }, { slug: "happy", label: "Felice" }, { slug: "party", label: "Festa" },
  { slug: "night", label: "Notte" }, { slug: "dreamy", label: "Sognante" }, { slug: "romantic", label: "Romantico" },
  { slug: "nostalgic", label: "Nostalgico" }, { slug: "sad", label: "Triste" }, { slug: "relax", label: "Relax" },
  { slug: "calm", label: "Calma" }, { slug: "focus", label: "Concentrazione" }, { slug: "epic", label: "Epico" },
];

export { genreImg, moodImg } from "./assets";
export const findGenre = (slug: string) => GENRES.find((g) => g.slug === slug);
export const findMood = (slug: string) => MOODS.find((m) => m.slug === slug);
