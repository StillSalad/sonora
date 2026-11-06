import { fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { META, feedPage, mockApi, renderAt, track } from "./utils";

let playSpy: ReturnType<typeof vi.spyOn>;
beforeEach(() => {
  playSpy = vi.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue(undefined);
  vi.spyOn(HTMLMediaElement.prototype, "pause").mockImplementation(() => {});
  vi.spyOn(HTMLMediaElement.prototype, "load").mockImplementation(() => {});
});

const base = (extra: (url: string, init?: RequestInit) => { status: number; body?: unknown } | undefined) =>
  (url: string, init?: RequestInit) => {
    if (url.endsWith("/meta")) return { status: 200, body: META };
    if (url.endsWith("/auth/me")) return { status: 401, body: {} };
    if (url.includes("/feed/events")) return { status: 202, body: { accepted: true } };
    return extra(url, init);
  };

describe("feed Per te", () => {
  it("mostra brani reali con spiegazione, fonte e link al servizio, senza audio automatico", async () => {
    mockApi(base((u) => (u.includes("/feed?") ? { status: 200, body: feedPage(0, 5) } : undefined)));
    renderAt("/");
    expect(await screen.findByRole("heading", { name: "Brano 0" })).toBeInTheDocument();
    expect(screen.getByText("Popolare in Italia: n. 1 su Apple Music")).toBeInTheDocument();
    expect(screen.getByText("Scoperta Pop fuori dalle classifiche attuali")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /Ascolta su Apple Music/ })[0]).toHaveAttribute("href", "https://music.apple.com/it/x/0");
    expect(screen.getAllByText("Anteprima di 30 secondi e copertina da Apple Music")[0]).toBeInTheDocument();
    expect(playSpy).not.toHaveBeenCalled();
  });

  it("il play avvia l’anteprima autorizzata e registra l’evento", async () => {
    const spy = mockApi(base((u) => (u.includes("/feed?") ? { status: 200, body: feedPage(0, 2, null) } : undefined)));
    renderAt("/");
    await userEvent.click(await screen.findByRole("button", { name: "Ascolta l’anteprima di Brano 0" }));
    const srcs = playSpy.mock.contexts.map((a) => (a as HTMLAudioElement).src);
    expect(srcs).toContain("https://audio.example/0.m4a");
    expect(srcs.filter((x) => x.startsWith("https://")).length).toBe(1);
    await waitFor(() => expect(spy.mock.calls.some(([u, i]) => String(u).endsWith("/feed/events") && String(i?.body).includes("preview_start"))).toBe(true));
  });

  it("senza diritto verificato il play è disattivato e lo dice", async () => {
    const page = feedPage(0, 1, null);
    page.items[0].track = track(0, { preview: { status: "RIGHTS_PENDING", url: null, duration_seconds: null, provider: "itunes" } }) as never;
    mockApi(base((u) => (u.includes("/feed?") ? { status: 200, body: page } : undefined)));
    renderAt("/");
    expect(await screen.findByRole("button", { name: "Anteprima non disponibile" })).toBeDisabled();
    expect(screen.getByText("Anteprima in verifica")).toBeInTheDocument();
  });

  it("catalogo vuoto: lo dice invece di inventare brani", async () => {
    mockApi(base((u) => (u.includes("/feed?") ? { status: 200, body: { ...feedPage(0, 0, null), exhausted: true } } : undefined)));
    renderAt("/");
    expect(await screen.findByRole("heading", { name: "Il catalogo è ancora vuoto" })).toBeInTheDocument();
  });

  it("mi piace da anonimo porta all’accesso", async () => {
    mockApi(base((u) => (u.includes("/feed?") ? { status: 200, body: feedPage(0, 1, null) } : undefined)));
    renderAt("/");
    await userEvent.click(await screen.findByRole("button", { name: "Mi piace" }));
    expect(await screen.findByRole("heading", { name: "Accedi" })).toBeInTheDocument();
  });
});

describe("ricerca e generi", () => {
  it("cerca dopo due lettere e mostra i risultati", async () => {
    const spy = mockApi(base((u) => (u.includes("/search?") ? { status: 200, body: { items: [track(7, { title: "Brava" })], live: "ok" } } : undefined)));
    renderAt("/cerca");
    fireEvent.change(await screen.findByRole("searchbox"), { target: { value: "mina" } });
    expect(await screen.findByText("Brava")).toBeInTheDocument();
    expect(spy.mock.calls.some(([u]) => String(u).includes("/search?q=mina"))).toBe(true);
  });

  it("se Apple non risponde lo segnala", async () => {
    mockApi(base((u) => (u.includes("/search?") ? { status: 200, body: { items: [], live: "unavailable" } } : undefined)));
    renderAt("/cerca");
    fireEvent.change(await screen.findByRole("searchbox"), { target: { value: "zzz" } });
    expect(await screen.findByText(/Apple Music non risponde/)).toBeInTheDocument();
  });

  it("la pagina genere elenca i brani del tag", async () => {
    mockApi(base((u) => (u.includes("/tags/rap/tracks") ? { status: 200, body: { tag: { slug: "rap" }, items: [track(1), track(2)], next_offset: null } } : undefined)));
    renderAt("/esplora/genere/rap");
    expect(await screen.findByText("Brano 2")).toBeInTheDocument();
  });

  it("i mood vuoti spiegano come si riempiono, senza inventarli", async () => {
    mockApi(base((u) => (u.includes("/tags/sad/tracks") ? { status: 200, body: { tag: { slug: "sad" }, items: [], next_offset: null } } : undefined)));
    renderAt("/esplora/mood/sad");
    expect(await screen.findByRole("heading", { name: "Ancora nessun brano triste" })).toBeInTheDocument();
  });

  it("i mood votati compaiono nella pagina mood", async () => {
    mockApi(base((u) => (u.includes("/tags/night/tracks?category=mood") ? { status: 200, body: { tag: { slug: "night" }, items: [track(3)], next_offset: null } } : undefined)));
    renderAt("/esplora/mood/night");
    expect(await screen.findByText("Brano 3")).toBeInTheDocument();
    expect(screen.getByText("Atmosfera votata da chi ascolta su SONORA.")).toBeInTheDocument();
  });
});
