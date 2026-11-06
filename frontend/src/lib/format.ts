import type { Track } from "./api";

export const artistNames = (t: Track) =>
  t.artists.filter((a) => a.role === "primary").map((a) => a.name).join(", ") || t.artists[0]?.name || "";
