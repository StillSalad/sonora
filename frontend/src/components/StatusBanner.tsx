import { useApp } from "../context/AppContext";
import { Icon } from "./Icon";

/** Stato reale della connessione: offline del dispositivo o server non raggiungibile, con riprova. */
export function StatusBanner() {
  const { online, backend, retry } = useApp();
  if (online && backend === "waking")
    return (
      <div role="status" className="sticky top-0 z-40 flex items-center gap-3 bg-surface2 px-4 py-2.5 pt-safe text-sm">
        <span className="h-4 w-4 flex-none animate-spin rounded-full border-2 border-muted/40 border-t-secondary" aria-hidden="true" />
        <p className="flex-1">SONORA si sta avviando: può volerci fino a un minuto.</p>
      </div>
    );
  if (online && backend !== "unreachable") return null;
  const text = import.meta.env.VITE_PREVIEW === "1"
    ? "Anteprima grafica senza server: accesso e dati personali non sono attivi qui."
    : !online
    ? "Sei offline. Puoi sfogliare ciò che è già salvato; il resto torna quando rientri in rete."
    : "Il server di SONORA non risponde. Accesso e dati personali non sono disponibili finché non torna.";
  return (
    <div role="status" className="sticky top-0 z-20 flex items-center gap-3 bg-surface2 px-4 py-2.5 pt-safe text-sm">
      <Icon name="offline" size={18} className="text-accent" />
      <p className="flex-1">{text}</p>
      {online && (
        <button onClick={retry} className="rounded-lg px-3 py-1.5 font-semibold text-secondary hover:bg-surface">
          Riprova
        </button>
      )}
    </div>
  );
}
