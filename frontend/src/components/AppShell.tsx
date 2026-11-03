import { logoFull } from "../lib/assets";
import { NavLink, Outlet, Link } from "react-router-dom";
import { Icon, type IconName } from "./Icon";
import { StatusBanner } from "./StatusBanner";

const NAV: { to: string; label: string; icon: IconName; end?: boolean }[] = [
  { to: "/", label: "Per te", icon: "home", end: true },
  { to: "/esplora", label: "Esplora", icon: "discover" },
  { to: "/cerca", label: "Cerca", icon: "search" },
  { to: "/raccolte", label: "Raccolte", icon: "collections" },
  { to: "/profilo", label: "Profilo", icon: "profile" },
];

export function AppShell() {
  return (
    <div className="min-h-dvh lg:flex">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded-lg focus:bg-surface focus:px-4 focus:py-2">
        Vai al contenuto
      </a>

      {/* barra laterale desktop */}
      <aside className="hidden lg:flex lg:w-64 lg:flex-col lg:gap-8 lg:border-r lg:border-surface2 lg:px-5 lg:py-8 sticky top-0 h-dvh">
        <Link to="/" aria-label="SONORA, vai a Per te">
          <img src={logoFull} alt="SONORA" className="h-9 w-auto" />
        </Link>
        <nav aria-label="Principale" className="flex flex-col gap-1">
          {NAV.map((n) => (
            <NavLink key={n.to} to={n.to} end={n.end}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-3 py-2.5 text-[15px] transition-colors ${isActive ? "bg-surface2 text-ink font-semibold" : "text-muted hover:text-ink hover:bg-surface"}`}>
              {({ isActive }) => (<><Icon name={n.icon} className={isActive ? "text-primary" : ""} />{n.label}</>)}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="flex-1 min-w-0">
        <StatusBanner />
        <main id="main" className="mx-auto w-full max-w-5xl px-4 pb-28 pt-safe sm:px-6 lg:pb-12">
          <Outlet />
        </main>
      </div>

      {/* barra in basso su mobile */}
      <nav aria-label="Principale" className="lg:hidden fixed inset-x-0 bottom-0 z-30 border-t border-surface2 bg-bg/90 backdrop-blur-md pb-safe">
        <ul className="mx-auto flex max-w-md justify-between px-2">
          {NAV.map((n) => (
            <li key={n.to} className="flex-1">
              <NavLink to={n.to} end={n.end}
                className={({ isActive }) => `flex flex-col items-center gap-1 py-2.5 text-[11px] ${isActive ? "text-ink font-semibold" : "text-muted"}`}>
                {({ isActive }) => (<><Icon name={n.icon} size={24} className={isActive ? "text-primary" : ""} />{n.label}</>)}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}
