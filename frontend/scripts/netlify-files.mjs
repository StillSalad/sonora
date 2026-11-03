// Eseguito da Netlify dopo la build: crea _redirects e _headers in dist/.
// Le chiamate /api/* vengono inoltrate al backend: stesso dominio per il browser, quindi i cookie
// di sessione funzionano anche su iPhone (niente cookie di terze parti).
import { writeFileSync } from "node:fs";

const api = (process.env.SONORA_API_ORIGIN || "").replace(/\/+$/, "");
if (!/^https:\/\/[^/]+$/.test(api)) {
  console.error("Manca SONORA_API_ORIGIN (es. https://sonora-api.onrender.com) nelle variabili d'ambiente di Netlify.");
  process.exit(1);
}
writeFileSync("dist/_redirects", `/api/*  ${api}/api/:splat  200!\n/*  /index.html  200\n`);
writeFileSync("dist/_headers", [
  "/sw.js", "  Cache-Control: no-cache", "",
  "/assets/*", "  Cache-Control: public, max-age=31536000, immutable", "",
  "/*", "  X-Content-Type-Options: nosniff", "  Referrer-Policy: strict-origin-when-cross-origin",
  "  Permissions-Policy: camera=(), microphone=(), geolocation=()", "",
].join("\n"));
console.log(`Redirect /api/* -> ${api}`);
