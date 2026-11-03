import type { ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext";
import type { Features } from "../lib/api";
import { Icon } from "./Icon";

export function PageTitle({ children, sub, back }: { children: ReactNode; sub?: ReactNode; back?: boolean }) {
  const nav = useNavigate();
  return (
    <header className="pb-6 pt-6 lg:pt-10">
      {back && (
        <button onClick={() => nav(-1)} className="-ml-2 mb-3 flex items-center gap-1 rounded-lg px-2 py-1 text-sm text-muted hover:text-ink">
          <Icon name="chevron_left" size={18} /> Indietro
        </button>
      )}
      <h1 className="text-[2rem] font-semibold leading-[1.05] tracking-[-0.02em] lg:text-[2.6rem]">{children}</h1>
      {sub && <p className="mt-2 max-w-prose text-muted">{sub}</p>}
    </header>
  );
}

/** Pannello onesto per le funzioni non ancora attive: niente pulsanti finti. */
export function NotActive({ feature, image, title, children, action }: {
  feature: keyof Features; image: string; title: string; children: ReactNode; action?: ReactNode;
}) {
  const { meta } = useApp();
  if (meta?.features[feature]) return null;
  return (
    <section className="flex flex-col items-center px-2 py-6 text-center">
      <img src={image} alt="" width={220} height={220} className="h-[220px] w-[220px]" />
      <h2 className="mt-2 text-xl font-semibold">{title}</h2>
      <p className="mt-2 max-w-sm text-muted">{children}</p>
      {action && <div className="mt-5">{action}</div>}
    </section>
  );
}

export function ButtonLink({ to, children, variant = "primary" }: { to: string; children: ReactNode; variant?: "primary" | "ghost" }) {
  return (
    <Link to={to} className={variant === "primary" ? btnPrimary : btnGhost}>
      {children}
    </Link>
  );
}

export const btnPrimary =
  "inline-flex items-center justify-center gap-2 rounded-full bg-primary px-5 py-3 font-semibold text-white transition hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed";
export const btnGhost =
  "inline-flex items-center justify-center gap-2 rounded-full border border-surface2 px-5 py-3 font-semibold text-ink transition hover:bg-surface";
export const field =
  "w-full rounded-xl border border-surface2 bg-surface px-4 py-3 text-ink placeholder:text-muted focus:border-secondary focus:outline-none";
