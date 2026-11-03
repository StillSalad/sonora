import { useEffect, useState } from "react";
import { Icon } from "./Icon";

type BIP = Event & { prompt: () => Promise<void>; userChoice: Promise<{ outcome: string }> };

/** Installazione PWA: prompt nativo dove esiste, istruzioni su iOS, niente se già installata. */
export function InstallButton() {
  const [evt, setEvt] = useState<BIP | null>(null);
  const [installed, setInstalled] = useState(
    typeof window !== "undefined" && window.matchMedia?.("(display-mode: standalone)").matches,
  );
  useEffect(() => {
    const onPrompt = (e: Event) => { e.preventDefault(); setEvt(e as BIP); };
    const onInstalled = () => setInstalled(true);
    window.addEventListener("beforeinstallprompt", onPrompt);
    window.addEventListener("appinstalled", onInstalled);
    return () => { window.removeEventListener("beforeinstallprompt", onPrompt); window.removeEventListener("appinstalled", onInstalled); };
  }, []);

  if (installed) return <Row text="SONORA è installata su questo dispositivo." />;
  if (evt)
    return (
      <button onClick={async () => { await evt.prompt(); await evt.userChoice; setEvt(null); }}
        className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left hover:bg-surface2">
        <Icon name="install" className="text-secondary" />
        <span className="flex-1 font-medium">Installa l’app</span>
      </button>
    );
  const ios = typeof navigator !== "undefined" && /iphone|ipad|ipod/i.test(navigator.userAgent);
  return <Row text={ios ? "Per installarla su iPhone: tocca Condividi in Safari, poi “Aggiungi alla schermata Home”."
    : "L’installazione si attiva quando il browser la consente (Chrome, Edge, Samsung Internet)."} />;
}

function Row({ text }: { text: string }) {
  return (
    <div className="flex items-start gap-3 px-4 py-3 text-sm text-muted">
      <Icon name="install" className="mt-0.5" />
      <p>{text}</p>
    </div>
  );
}
