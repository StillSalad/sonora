// Ogni asset è un file separato in src/assets; Vite li versiona (nome con hash) al build.
const pick = (mods: Record<string, string>, re: RegExp) =>
  Object.fromEntries(Object.entries(mods).map(([path, url]) => [path.match(re)![1], url]));

const categories = pick(import.meta.glob("../assets/categories/*.png", { eager: true, import: "default", query: "?url" }) as Record<string, string>, /category_(.+)\.png$/);
const moods = pick(import.meta.glob("../assets/moods/*.png", { eager: true, import: "default", query: "?url" }) as Record<string, string>, /mood_(.+)\.png$/);
const states = pick(import.meta.glob("../assets/states/*.png", { eager: true, import: "default", query: "?url" }) as Record<string, string>, /state_(.+)\.png$/);
const icons = pick(import.meta.glob("../assets/icons/*.svg", { eager: true, import: "default", query: "?url" }) as Record<string, string>, /icon_(.+)\.svg$/);
const brand = pick(import.meta.glob("../assets/brand/*.png", { eager: true, import: "default", query: "?url" }) as Record<string, string>, /brand\/(.+)\.png$/);

export const genreImg = (slug: string) => categories[slug];
export const moodImg = (slug: string) => moods[slug];
export const stateImg = (slug: "empty_favorites" | "loading_music" | "hidden_gems" | "music_dna") => states[slug];
export const iconUrl = (name: string) => icons[name];
export const logoFull = brand["sonora_logo_full"];
