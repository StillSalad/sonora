import "@fontsource-variable/bricolage-grotesque";
import "@fontsource-variable/figtree";
import "./index.css";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, MemoryRouter } from "react-router-dom";
import App from "./App";
import { AppProvider } from "./context/AppContext";
import { PlayerProvider } from "./context/PlayerContext";

const PREVIEW = import.meta.env.VITE_PREVIEW === "1";
const Router = PREVIEW ? MemoryRouter : BrowserRouter;

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AppProvider>
        <PlayerProvider>
          <App />
        </PlayerProvider>
      </AppProvider>
    </Router>
  </StrictMode>,
);

// Il service worker si registra solo dove è supportato; gli aggiornamenti si applicano al prossimo avvio.
if (!PREVIEW && "serviceWorker" in navigator) {
  import("virtual:pwa-register").then(({ registerSW }) => registerSW({ immediate: true })).catch(() => {});
}
