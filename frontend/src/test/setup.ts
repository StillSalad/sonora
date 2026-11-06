import "@testing-library/jest-dom/vitest";
import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

import { beforeEach } from "vitest";
import { setPrefs } from "../lib/prefs";

// di default la scelta iniziale è già fatta: i test della scelta la azzerano
beforeEach(() => { localStorage.clear(); setPrefs({ done: true, genres: [], artists: [] }); localStorage.setItem("sonora-daily-shown", new Date().toISOString().slice(0, 10)); });
afterEach(() => { cleanup(); vi.restoreAllMocks(); });
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: (q: string) => ({ matches: false, media: q, addEventListener() {}, removeEventListener() {}, onchange: null, addListener() {}, removeListener() {}, dispatchEvent: () => false }),
});
