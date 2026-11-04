export const API_BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "/api/v1";

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string, public fields: { field: string; message: string }[] = []) {
    super(message);
  }
}

/** Identificativo casuale del dispositivo (nessun dato personale): il feed lo usa per non
 *  riproporre i brani già visti nelle sessioni precedenti, anche senza account. */
function deviceId(): string | null {
  try {
    let id = localStorage.getItem("sonora-device");
    if (!id) {
      id = typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : Array.from({ length: 32 }, () => Math.floor(Math.random() * 16).toString(16)).join("");
      localStorage.setItem("sonora-device", id);
    }
    return id;
  } catch {
    return null;
  }
}

export async function api<T>(path: string, init: RequestInit & { json?: unknown } = {}): Promise<T> {
  const { json, headers, ...rest } = init;
  let res: Response;
  try {
    res = await fetch(API_BASE + path, {
      credentials: "include",
      ...rest,
      headers: {
        "X-Sonora-Client": "web",
        ...(path.startsWith("/feed") && deviceId() ? { "X-Sonora-Device": deviceId()! } : {}),
        ...(json !== undefined ? { "Content-Type": "application/json" } : {}),
        ...headers,
      },
      body: json !== undefined ? JSON.stringify(json) : rest.body,
    });
  } catch {
    throw new ApiError(0, "network", "Server non raggiungibile.");
  }
  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    throw new ApiError(res.status, data?.code ?? "error", data?.message ?? "Qualcosa non ha funzionato.", data?.fields ?? []);
  }
  return data as T;
}

export type User = {
  id: string; email: string; username: string; display_name: string;
  avatar_url: string | null; role: string; is_private: boolean; created_at: string;
};
export type Features = Record<
  | "auth" | "catalog" | "search" | "feed" | "previews" | "likes" | "genre_pages" | "tags" | "collections"
  | "music_dna" | "community" | "integrations" | "admin",
  boolean
>;
export type Meta = {
  name: string; version: string; environment: string; milestone: number; features: Features;
  store_country: string; demo_mode: boolean;
};

export type PreviewStatus = "AVAILABLE" | "UNAVAILABLE" | "EXTERNAL_ONLY" | "RIGHTS_PENDING" | "BLOCKED";
export type Track = {
  id: string; title: string;
  artists: { id: string; name: string; role: string }[];
  album: { id: string; title: string } | null;
  release_year: number | null; duration_ms: number | null; explicit: boolean;
  artwork: { url: string; attribution: string } | null;
  tags: { slug: string; label: string; category: string; origin: string }[];
  popularity: { class: "popular" | "discovery" | "unknown"; score: number | null; confidence: number | null; sources: Record<string, unknown>[] };
  preview: { status: PreviewStatus; url: string | null; duration_seconds: number | null; provider: string | null };
  links: { provider: string; label: string; url: string }[];
  liked: boolean; demo: boolean;
};
export type FeedItem = { position: number; slot: "popular" | "discovery"; tolerance: boolean; explanation: string | null; reasons: string[]; track: Track };
export type FeedPage = {
  items: FeedItem[]; next_cursor: string | null; session_id: string; exhausted: boolean;
  window: { size: number; popular: number; discovery: number };
};

/** Segnali al backend: non bloccano mai l'interfaccia. */
export function sendEvent(track_id: string, event_type: string, extra: { listened_ms?: number; session_id?: string; source_surface?: string } = {}) {
  void api("/feed/events", { method: "POST", json: { track_id, event_type, ...extra } }).catch(() => {});
}
