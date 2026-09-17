import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

/** Sidebar + content column shared by the configuration pages. */
export function AdminShell({ children }: { children: ReactNode }) {
  return (
    <div className="admin">
      <nav className="side" aria-label="Configuration">
        <div className="eyebrow">Configuration</div>
        <NavLink to="/admin/rules">Rules</NavLink>
        <NavLink to="/admin/claims">Claims</NavLink>
        <NavLink to="/admin/data">Data &amp; deploy</NavLink>
        <div className="foot">
          Changes write to <span className="mono">rules/</span>, <span className="mono">claims/</span> and the
          data bucket. The runner re-scores on next run.
        </div>
      </nav>
      <div className="content">{children}</div>
    </div>
  );
}
