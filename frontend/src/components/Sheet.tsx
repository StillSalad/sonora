import { useEffect, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { Icon } from "./Icon";

/** Pannello che sale dal basso (menu della scheda, voto dell'atmosfera). Esc o tocco fuori per chiudere. */
export function Sheet({ open, title, onClose, children }: { open: boolean; title: string; onClose: () => void; children: ReactNode }) {
  const panel = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const prev = document.activeElement as HTMLElement | null;
    panel.current?.querySelector<HTMLElement>("button, a, input")?.focus();
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("keydown", onKey); prev?.focus?.(); };
  }, [open, onClose]);
  if (!open) return null;
  // disegnato direttamente nel body: nessun contenitore (feed, barra di navigazione) può coprirlo
  return createPortal(
    <div className="fixed inset-0 z-50 flex items-end justify-center lg:items-center" role="presentation">
      <button aria-label="Chiudi" tabIndex={-1} onClick={onClose} className="absolute inset-0 bg-black/55 backdrop-blur-[2px]" />
      <div ref={panel} role="dialog" aria-modal="true" aria-label={title}
        className="sheet-in relative w-full max-w-md rounded-t-[1.75rem] bg-surface px-3 pb-[calc(env(safe-area-inset-bottom)+0.75rem)] pt-2 shadow-2xl lg:rounded-[1.75rem] lg:pb-3">
        <div aria-hidden="true" className="mx-auto mb-2 h-1.5 w-10 rounded-full bg-surface2 lg:hidden" />
        <div className="flex items-center justify-between px-2 pb-1">
          <h2 className="truncate text-[17px] font-semibold">{title}</h2>
          <button onClick={onClose} aria-label="Chiudi" className="grid h-10 w-10 place-items-center rounded-full hover:bg-surface2">
            <Icon name="close" size={20} />
          </button>
        </div>
        {children}
      </div>
    </div>,
    document.body,
  );
}

export function SheetAction({ icon, label, hint, onClick, danger }: {
  icon: Parameters<typeof Icon>[0]["name"]; label: string; hint?: string; onClick: () => void; danger?: boolean;
}) {
  return (
    <button onClick={onClick} className={`flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-left hover:bg-surface2 ${danger ? "text-danger" : ""}`}>
      <Icon name={icon} size={22} className={danger ? "" : "text-muted"} />
      <span className="min-w-0 flex-1">
        <span className="block truncate font-medium">{label}</span>
        {hint && <span className="block truncate text-sm text-muted">{hint}</span>}
      </span>
    </button>
  );
}
