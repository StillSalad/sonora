import { act, fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getPrefs, setPrefs } from "../lib/prefs";
import { META, USER, feedPage, mockApi, renderAt, track } from "./utils";

beforeEach(() => {
  vi.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue(undefined);
  vi.spyOn(HTMLMediaElement.prototype, "pause").mockImplementation(() => {});
  vi.spyOn(HTMLMediaElement.prototype, "load").mockImplementation(() => {});
});

type H = (url: string, init?: RequestInit) => { status: number; body?: unknown } | undefined;
const base = (extra: H, logged = false): H => (url, init) => {
  if (url.endsWith("/meta")) return { status: 200, body: META };
  if (url.endsWith("/auth/me")) return logged ? { status: 200, body: USER } : { status: 401, body: {} };
  if (url.includes("/feed/events")) return { status: 202, body: {} };
  return extra(url, init);
};

describe("scelta iniziale", () => {
  it("al primo avvio porta alla scelta e poi personalizza il feed", async () => {
    setPrefs({ done: false, genres: [], artists: [] });
    const spy = mockApi(base((u) => {
      if (u.includes("/onboarding/artists")) return { status: 200, body: { items: [{ id: "a1", name: "Mina", genre: "pop", genre_label: "Pop", artwork_url: null }] } };
      if (u.includes("/feed?")) return { status: 200, body: feedPage(0, 3, null) };
    }));
    renderAt("/");
    expect(await screen.findByRole("heading", { name: "Cosa ascolti di solito?" })).toBeInTheDocument();
    const user = userEvent.setup();
    const next = screen.getByRole("button", { name: /Scegline ancora 3/ });
    expect(next).toBeDisabled();
    for (const g of ["Pop", "Rap", "Jazz"]) await user.click(screen.getByRole("button", { name: g }));
    await user.click(screen.getByRole("button", { name: "Avanti (3)" }));
    await user.click(await screen.findByRole("button", { name: /Mina/ }));
    await user.click(screen.getByRole("button", { name: "Fatto (1)" }));
    expect(await screen.findByRole("heading", { name: "Brano 0" })).toBeInTheDocument();
    expect(getPrefs()).toEqual({ done: true, genres: ["pop", "rap", "jazz"], artists: [{ id: "a1", name: "Mina" }] });
    const feedCall = spy.mock.calls.map(([u]) => String(u)).find((u) => u.includes("/feed?"))!;
    expect(feedCall).toContain("g=pop%2Crap%2Cjazz");
    expect(feedCall).toContain("a=a1");
  });

  it("si può saltare", async () => {
    setPrefs({ done: false, genres: [], artists: [] });
    mockApi(base((u) => (u.includes("/feed?") ? { status: 200, body: feedPage(0, 1, null) } : undefined)));
    renderAt("/");
    await userEvent.click(await screen.findByRole("button", { name: "Salta" }));
    expect(await screen.findByRole("heading", { name: "Brano 0" })).toBeInTheDocument();
  });
});

describe("gesti e menu", () => {
  const feedOnly: H = (u) => (u.includes("/feed?") ? { status: 200, body: feedPage(0, 3, null) } : undefined);

  it("doppio tocco sulla copertina mette Mi piace", async () => {
    const spy = mockApi(base((u, i) => {
      if (u.includes("/tracks/t0/like") && i?.method === "POST") return { status: 204 };
      return feedOnly(u, i);
    }, true));
    renderAt("/");
    const card = await screen.findByRole("region", { name: "Brano 0 di Artista 0" }).catch(() => null)
      ?? (await screen.findByRole("heading", { name: "Brano 0" })).closest("section")!;
    const surface = card.querySelector(".gesture-surface")!;
    await waitFor(() => expect(within(card as HTMLElement).getByRole("button", { name: "Mi piace" })).toBeInTheDocument());
    fireEvent.pointerDown(surface); fireEvent.pointerUp(surface);
    fireEvent.pointerDown(surface); fireEvent.pointerUp(surface);
    await waitFor(() => expect(spy.mock.calls.some(([u, i]) => String(u).endsWith("/tracks/t0/like") && i?.method === "POST")).toBe(true));
    expect(within(card as HTMLElement).getByRole("button", { name: "Togli da Mi piace" })).toHaveAttribute("aria-pressed", "true");
  });

  it("tieni premuto: Non mi interessa, poi Annulla", async () => {
    const spy = mockApi(base((u, i) => {
      if (u.endsWith("/feed/feedback") && i?.method === "POST") return { status: 201, body: { id: "fb1", kind: "not_interested", genre: null, artist_id: null } };
      if (u.endsWith("/feed/feedback/fb1") && i?.method === "DELETE") return { status: 204 };
      return feedOnly(u, i);
    }));
    renderAt("/");
    const card = (await screen.findByRole("heading", { name: "Brano 0" })).closest("section")!;
    const surface = card.querySelector(".gesture-surface")!;
    fireEvent.pointerDown(surface);
    await act(() => new Promise((r) => setTimeout(r, 560)));
    fireEvent.pointerUp(surface);
    const dialog = await screen.findByRole("dialog", { name: "Brano 0" });
    expect(within(dialog).getByRole("button", { name: /Meno brani Pop/ })).toBeInTheDocument();
    await userEvent.click(within(dialog).getByRole("button", { name: /Non mi interessa/ }));
    expect(await screen.findByText("Non lo vedrai più")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Annulla" }));
    expect(await screen.findByRole("heading", { name: "Brano 0" })).toBeInTheDocument();
    expect(spy.mock.calls.some(([u, i]) => String(u).endsWith("/feed/feedback/fb1") && i?.method === "DELETE")).toBe(true);
  });

  it("il pulsante ⋯ apre lo stesso menu (accessibile senza gesti)", async () => {
    mockApi(base(feedOnly));
    renderAt("/");
    await screen.findByRole("heading", { name: "Brano 0" });
    await userEvent.click(screen.getAllByRole("button", { name: "Altre azioni" })[0]);
    expect(await screen.findByRole("dialog", { name: "Brano 0" })).toBeInTheDocument();
  });

  it("condividi offre link e storia", async () => {
    mockApi(base(feedOnly));
    renderAt("/");
    await screen.findByRole("heading", { name: "Brano 0" });
    await userEvent.click(screen.getAllByRole("button", { name: "Condividi" })[0]);
    const d = await screen.findByRole("dialog", { name: "Condividi" });
    expect(within(d).getByRole("button", { name: /Condividi il link/ })).toBeInTheDocument();
    expect(within(d).getByRole("button", { name: /Condividi come storia/ })).toBeInTheDocument();
  });
});

describe("scoperta del giorno e simili", () => {
  it("la scoperta del giorno compare in testa una volta al giorno", async () => {
    localStorage.removeItem("sonora-daily-shown");
    const daily = { position: -1, slot: "daily", tolerance: false, explanation: "Scoperta del giorno, scelta per te", reasons: [], track: track(99, { title: "Gemma" }) };
    mockApi(base((u) => {
      if (u.includes("/feed/daily")) return { status: 200, body: { date: "2026-11-04", item: daily } };
      if (u.includes("/feed?")) return { status: 200, body: feedPage(0, 3, null) };
    }));
    renderAt("/");
    const first = (await screen.findByRole("heading", { name: "Gemma" })).closest("section")!;
    expect(first.getAttribute("data-index")).toBe("0");
    expect(within(first as HTMLElement).getByText("Scoperta del giorno")).toBeInTheDocument();
  });

  it("Altri brani così apre il mini feed", async () => {
    mockApi(base((u) => {
      if (u.includes("/feed?")) return { status: 200, body: feedPage(0, 2, null) };
      if (u.includes("/tracks/t0/similar")) return { status: 200, body: { seed: track(0), items: [{ position: 0, slot: "similar", tolerance: false, explanation: "Stesso genere: Pop", reasons: [], track: track(50, { title: "Simile" }) }] } };
    }));
    renderAt("/");
    await screen.findByRole("heading", { name: "Brano 0" });
    await userEvent.click(screen.getAllByRole("button", { name: /Altri brani così/ })[0]);
    expect(await screen.findByRole("heading", { name: "Simile" })).toBeInTheDocument();
    expect(screen.getByText("Stesso genere: Pop")).toBeInTheDocument();
  });

  it("voto dell'atmosfera: da anonimo chiede l'accesso", async () => {
    mockApi(base((u) => {
      if (u.includes("/feed?")) return { status: 200, body: feedPage(0, 1, null) };
      if (u.includes("/tracks/t0/moods")) return { status: 200, body: { voters: 0, moods: [], mine: [] } };
    }));
    renderAt("/");
    await screen.findByRole("heading", { name: "Brano 0" });
    await userEvent.click(screen.getByRole("button", { name: "Altre azioni" }));
    await userEvent.click(await screen.findByRole("button", { name: /Che atmosfera ha/ }));
    const d = await screen.findByRole("dialog", { name: "Che atmosfera ha?" });
    expect(within(d).getByText(/Per votare serve un account/)).toBeInTheDocument();
    expect(within(d).getByRole("button", { name: /Notte/ })).toBeDisabled();
  });
});
