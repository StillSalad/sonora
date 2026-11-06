import { artistNames } from "./format";
import { logoFull } from "./assets";
import type { Track } from "./api";

/** Immagine verticale 1080×1920 per le storie (Instagram, WhatsApp…). Copertina dal provider, titolo,
 *  artista e logo SONORA. Se la copertina non può essere usata nel disegno, esce senza copertina. */
function loadImage(src: string, cors: boolean): Promise<HTMLImageElement> {
  return new Promise((res, rej) => {
    const img = new Image();
    if (cors) img.crossOrigin = "anonymous";
    img.onload = () => res(img);
    img.onerror = () => rej(new Error("immagine"));
    img.src = src;
  });
}

function wrap(ctx: CanvasRenderingContext2D, text: string, max: number, lines: number): string[] {
  const words = text.split(/\s+/);
  const out: string[] = [];
  let line = "";
  for (const w of words) {
    const test = line ? `${line} ${w}` : w;
    if (ctx.measureText(test).width > max && line) { out.push(line); line = w; } else line = test;
  }
  if (line) out.push(line);
  if (out.length > lines) { out.length = lines; out[lines - 1] = out[lines - 1].replace(/\s*\S*$/, "") + "…"; }
  return out;
}

async function draw(t: Track, withCover: boolean): Promise<Blob> {
  const W = 1080, H = 1920;
  const c = document.createElement("canvas");
  c.width = W; c.height = H;
  const ctx = c.getContext("2d")!;
  await document.fonts?.ready;
  ctx.fillStyle = "#0B0D14"; ctx.fillRect(0, 0, W, H);
  const cover = withCover && t.artwork ? await loadImage(t.artwork.url, true) : null;
  if (cover) {
    ctx.save(); ctx.filter = "blur(70px) saturate(1.2)"; ctx.globalAlpha = 0.55;
    ctx.drawImage(cover, -300, -300, W + 600, H + 600); ctx.restore();
  } else {
    const g = ctx.createRadialGradient(200, 400, 50, 200, 400, 1300);
    g.addColorStop(0, "rgba(139,92,246,.55)"); g.addColorStop(1, "rgba(139,92,246,0)");
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  }
  const shade = ctx.createLinearGradient(0, 0, 0, H);
  shade.addColorStop(0, "rgba(11,13,20,.15)"); shade.addColorStop(1, "rgba(11,13,20,.9)");
  ctx.fillStyle = shade; ctx.fillRect(0, 0, W, H);
  const S = 800, x = (W - S) / 2, y = 330;
  ctx.save();
  ctx.beginPath(); ctx.roundRect(x, y, S, S, 48); ctx.clip();
  if (cover) ctx.drawImage(cover, x, y, S, S);
  else { ctx.fillStyle = "#202638"; ctx.fillRect(x, y, S, S); }
  ctx.restore();
  ctx.fillStyle = "#F5F6FA"; ctx.textAlign = "left";
  ctx.font = '600 76px "Bricolage Grotesque Variable", system-ui, sans-serif';
  const lines = wrap(ctx, t.title, S, 2);
  lines.forEach((l, i) => ctx.fillText(l, x, y + S + 120 + i * 86));
  ctx.font = '500 46px "Figtree Variable", system-ui, sans-serif';
  ctx.fillStyle = "#C9CDD8";
  ctx.fillText(wrap(ctx, artistNames(t) ?? "", S, 1)[0] ?? "", x, y + S + 120 + lines.length * 86 + 10);
  const logo = await loadImage(logoFull, false).catch(() => null);
  if (logo) { const lw = 360, lh = (logo.height / logo.width) * lw; ctx.drawImage(logo, (W - lw) / 2, H - 230, lw, lh); }
  ctx.font = '500 34px "Figtree Variable", system-ui, sans-serif'; ctx.fillStyle = "#969DB0"; ctx.textAlign = "center";
  ctx.fillText("Scoperto su SONORA", W / 2, H - 110);
  return await new Promise<Blob>((res, rej) => c.toBlob((b) => (b ? res(b) : rej(new Error("toBlob"))), "image/png"));
}

export async function makeStory(t: Track): Promise<{ blob: Blob; withCover: boolean }> {
  try { return { blob: await draw(t, true), withCover: !!t.artwork }; }
  catch { return { blob: await draw(t, false), withCover: false }; } // copertina non utilizzabile nel disegno
}

export async function shareStory(t: Track): Promise<"shared" | "downloaded"> {
  const { blob } = await makeStory(t);
  const file = new File([blob], `sonora-${t.title.replace(/[^\p{L}\p{N}]+/gu, "-").toLowerCase()}.png`, { type: "image/png" });
  const link = t.links[0]?.url;
  if (navigator.canShare?.({ files: [file] })) {
    await navigator.share({ files: [file], title: t.title, text: link ? `${t.title} di ${artistNames(t)} ${link}` : t.title });
    return "shared";
  }
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = file.name; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 4000);
  return "downloaded";
}
