/// <reference types="vitest" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";
import { viteSingleFile } from "vite-plugin-singlefile";

// `npm run build:preview` crea un unico file HTML autonomo per l'anteprima (senza service worker).
const PREVIEW = process.env.SONORA_PREVIEW === "1";

export default defineConfig({
  define: { "import.meta.env.VITE_PREVIEW": JSON.stringify(PREVIEW ? "1" : "") },
  build: PREVIEW ? { outDir: "dist-preview", assetsInlineLimit: 100_000_000 } : {},
  resolve: PREVIEW ? { alias: { "virtual:pwa-register": "/src/lib/pwa-stub.ts" } } : {},
  plugins: [
    react(),
    PREVIEW && viteSingleFile(),
    !PREVIEW && VitePWA({
      registerType: "prompt",
      includeAssets: ["favicon.svg", "icons/apple-touch-icon.png"],
      manifest: {
        name: "SONORA",
        short_name: "SONORA",
        description: "Scopri musica nuova tra brani famosi e gemme nascoste.",
        lang: "it",
        start_url: "/",
        scope: "/",
        display: "standalone",
        orientation: "portrait",
        background_color: "#0B0D14",
        theme_color: "#0B0D14",
        icons: [
          { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
          { src: "/icons/icon-maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
        ],
      },
      workbox: {
        // Solo app shell e asset statici. Nessun audio viene mai messo in cache.
        // Shell leggera in precache; le illustrazioni si salvano man mano che vengono viste.
        globPatterns: ["**/*.{js,css,html}", "assets/*-latin-*.woff2", "assets/icon_*.svg", "assets/sonora_logo_full-*.png", "assets/state_loading_music-*.png", "favicon.svg"],
        navigateFallback: "/index.html",
        navigateFallbackDenylist: [/^\/api\//],
        runtimeCaching: [
          {
            urlPattern: ({ url }) => url.pathname.startsWith("/assets/") && url.pathname.endsWith(".png"),
            handler: "CacheFirst",
            options: { cacheName: "sonora-illustrations", expiration: { maxEntries: 80 } },
          },
          {
            urlPattern: ({ url }) => url.pathname === "/api/v1/meta",
            handler: "NetworkFirst",
            options: { cacheName: "sonora-meta", networkTimeoutSeconds: 4 },
          },
        ],
      },
    }),
  ],
  server: { proxy: { "/api": { target: "http://localhost:8000", changeOrigin: false } } },
  preview: { proxy: { "/api": { target: "http://localhost:8000", changeOrigin: false } } },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.ts",
    css: false,
  },
});
