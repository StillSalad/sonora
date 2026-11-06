import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";
import App from "../App";
import { AppProvider } from "../context/AppContext";
import { PlayerProvider } from "../context/PlayerContext";

export const META = {
  name: "SONORA", version: "0.1.0", environment: "test", milestone: 1,
  store_country: "IT", demo_mode: false,
  features: { auth: true, catalog: true, search: true, feed: true, previews: true, likes: true, genre_pages: true, tags: true, collections: false, music_dna: false, community: false, integrations: false, admin: false, onboarding: true, feedback: true, daily: true, similar: true, mood_votes: true },
};
export function track(i: number, over: Record<string, unknown> = {}) {
  return {
    id: `t${i}`, title: `Brano ${i}`, artists: [{ id: `a${i}`, name: `Artista ${i}`, role: "primary" }],
    album: { id: `al${i}`, title: `Album ${i}` }, release_year: 2024, duration_ms: 200000, explicit: false,
    artwork: { url: `https://img.example/${i}.jpg`, attribution: "Apple Music" },
    tags: [{ slug: "pop", label: "Pop", category: "genre", origin: "provider" }],
    popularity: { class: "popular", score: 0.9, confidence: 0.9, sources: [] },
    preview: { status: "AVAILABLE", url: `https://audio.example/${i}.m4a`, duration_seconds: 30, provider: "itunes" },
    links: [{ provider: "apple_music", label: "Ascolta su Apple Music", url: `https://music.apple.com/it/x/${i}` }],
    liked: false, demo: false, ...over,
  };
}
export function feedPage(start: number, n: number, cursor: string | null = "c1") {
  return {
    items: Array.from({ length: n }, (_, k) => {
      const pos = start + k;
      const disc = pos % 5 === 4;
      return { position: pos, slot: disc ? "discovery" : "popular", tolerance: false,
        explanation: disc ? "Scoperta Pop fuori dalle classifiche attuali" : `Popolare in Italia: n. ${pos + 1} su Apple Music`,
        reasons: [], track: track(pos) };
    }),
    next_cursor: cursor, session_id: "s", exhausted: cursor === null, window: { size: n, popular: n, discovery: 0 },
  };
}

export const USER = { id: "1", email: "ada@example.com", username: "ada", display_name: "Ada", avatar_url: null, role: "user", is_private: true, created_at: "2026-11-02T00:00:00Z" };

type Handler = (url: string, init?: RequestInit) => { status: number; body?: unknown } | undefined;

export function mockApi(handler: Handler) {
  return vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const url = String(input);
    if (url.endsWith("/auth/session")) {
      const me = handler(url.replace("/auth/session", "/auth/me"), init);
      if (!me) throw new TypeError("network");
      return new Response(JSON.stringify({ user: me.status === 200 ? me.body : null }), { status: 200, headers: { "Content-Type": "application/json" } });
    }
    const r = handler(url, init);
    if (!r) throw new TypeError("network");
    return new Response(r.status === 204 ? null : JSON.stringify(r.body ?? {}), { status: r.status, headers: { "Content-Type": "application/json" } });
  });
}

export function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AppProvider><PlayerProvider><App /></PlayerProvider></AppProvider>
    </MemoryRouter>,
  );
}
