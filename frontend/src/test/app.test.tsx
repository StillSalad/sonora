import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { META, USER, mockApi, renderAt } from "./utils";

const anon = (url: string) => {
  if (url.endsWith("/meta")) return { status: 200, body: META };
  if (url.endsWith("/auth/me")) return { status: 401, body: { code: "unauthorized", message: "Accedi per continuare." } };
};

describe("SONORA shell", () => {
  it("Esplora elenca tutti i 27 generi e i 12 mood", async () => {
    mockApi(anon);
    renderAt("/esplora");
    const genres = await screen.findByRole("heading", { name: "Generi" });
    const list = genres.parentElement!.querySelector("ul")!;
    expect(within(list).getAllByRole("link")).toHaveLength(27);
    expect(within(screen.getByRole("heading", { name: "Mood" }).parentElement!.querySelector("ul")!).getAllByRole("link")).toHaveLength(12);
  });

  it("se il server non risponde avvisa che si sta avviando (piano gratuito)", async () => {
    mockApi(() => undefined);
    renderAt("/");
    expect(await screen.findByText(/SONORA si sta avviando/)).toBeInTheDocument();
  });

  it("slug sconosciuto porta alla pagina non trovata", async () => {
    mockApi(anon);
    renderAt("/esplora/genere/inesistente");
    expect(await screen.findByRole("heading", { name: "Pagina non trovata" })).toBeInTheDocument();
  });
});

describe("account", () => {
  it("accesso: invia le credenziali con l'header anti-CSRF e porta al profilo", async () => {
    let loggedIn = false;
    const spy = mockApi((url, init) => {
      if (url.endsWith("/meta")) return { status: 200, body: META };
      if (url.endsWith("/auth/me")) return loggedIn ? { status: 200, body: USER } : { status: 401, body: {} };
      if (url.endsWith("/auth/login") && init?.method === "POST") { loggedIn = true; return { status: 200, body: USER }; }
    });
    renderAt("/accedi");
    const user = userEvent.setup();
    await user.type(await screen.findByLabelText("Email"), "ada@example.com");
    await user.type(screen.getByLabelText("Password"), "password-lunga-1");
    await waitFor(() => expect(screen.getByRole("button", { name: "Accedi" })).toBeEnabled());
    await user.click(screen.getByRole("button", { name: "Accedi" }));
    expect(await screen.findByRole("heading", { name: "Ada" })).toBeInTheDocument();
    const call = spy.mock.calls.find(([u]) => String(u).endsWith("/auth/login"))!;
    expect((call[1]!.headers as Record<string, string>)["X-Sonora-Client"]).toBe("web");
    expect(call[1]!.credentials).toBe("include");
  });

  it("registrazione: mostra gli errori di campo del server", async () => {
    mockApi((url) => {
      if (url.endsWith("/meta")) return { status: 200, body: META };
      if (url.endsWith("/auth/me")) return { status: 401, body: {} };
      if (url.endsWith("/auth/register"))
        return { status: 422, body: { code: "validation_error", message: "Alcuni campi non sono validi.", fields: [{ field: "username", message: "Value error, Usa 3–32 caratteri" }] } };
    });
    renderAt("/registrati");
    const user = userEvent.setup();
    const submit = await screen.findByRole("button", { name: "Crea account" });
    expect(submit).toBeDisabled(); // serve la conferma dell'età
    await user.type(screen.getByLabelText("Nome"), "Ada");
    await user.type(screen.getByLabelText("Nome utente"), "A B");
    await user.type(screen.getByLabelText("Email"), "ada@example.com");
    await user.type(screen.getByLabelText("Password"), "password-lunga-1");
    await user.click(screen.getByRole("checkbox"));
    await user.click(submit);
    expect(await screen.findByText("Usa 3–32 caratteri")).toBeInTheDocument();
  });

  it("le raccolte chiedono l'accesso agli utenti anonimi", async () => {
    mockApi(anon);
    renderAt("/raccolte");
    expect(await screen.findByRole("heading", { name: "Accedi per salvare i brani" })).toBeInTheDocument();
  });
});
