import type { CSSProperties } from "react";
import { iconUrl } from "../lib/assets";

export type IconName =
  | "discover" | "trending" | "hidden_gems" | "daily_mix" | "random" | "collections" | "music_dna"
  | "artist" | "album" | "playlist" | "add" | "preview" | "share" | "filter" | "search"
  | "more" | "check" | "close" | "play" | "pause" | "heart" | "heart_filled" | "volume" | "volume_off"
  | "home" | "profile" | "sun" | "moon" | "chevron_left" | "external_link" | "logout" | "offline" | "install" | "link";

/** Icona da file SVG separato, colorata con il colore del testo (currentColor). */
export function Icon({ name, size = 24, className = "" }: { name: IconName; size?: number; className?: string }) {
  const style = { width: size, height: size, "--icon": `url("${iconUrl(name)}")` } as CSSProperties;
  return <span aria-hidden="true" className={`icon ${className}`} style={style} />;
}
