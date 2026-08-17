import { NavLink, useLocation } from "react-router-dom";
import { AgentPage } from "../pages/AgentPage";
import { ObservabilityPage } from "../pages/ObservabilityPage";

export function Layout() {
  const location = useLocation();
  const onObservability = location.pathname.startsWith("/observability");

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)]">
      <header className="flex items-center justify-between border-b border-[var(--border)] px-5 py-3">
        <div>
          <div className="text-sm font-semibold tracking-wide">AgentLens</div>
          <div className="text-xs text-[var(--muted)]">Build with AI. See what it costs.</div>
        </div>
        <nav className="flex gap-1 rounded-lg border border-[var(--border)] bg-[var(--panel)] p-1">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `rounded-md px-3 py-1.5 text-sm ${isActive ? "bg-[var(--accent)] text-black" : "text-[var(--muted)] hover:text-white"}`
            }
          >
            Agent
          </NavLink>
          <NavLink
            to="/observability"
            className={({ isActive }) =>
              `rounded-md px-3 py-1.5 text-sm ${isActive ? "bg-[var(--accent)] text-black" : "text-[var(--muted)] hover:text-white"}`
            }
          >
            Observability
          </NavLink>
        </nav>
      </header>
      <div className={onObservability ? "hidden" : "block"}>
        <AgentPage />
      </div>
      {onObservability ? <ObservabilityPage /> : null}
    </div>
  );
}
