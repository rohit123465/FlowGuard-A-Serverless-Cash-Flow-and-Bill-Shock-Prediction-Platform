import { Outlet } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Navigation } from "./Navigation";

export function Layout() {
  const { user, signOut } = useAuth();
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark small" aria-hidden="true">FG</div>
          <div><strong>FlowGuard</strong><span>Financial control</span></div>
        </div>
        <Navigation />
        <div className="sidebar-footer">
          <span className="status-dot" />
          <div><strong>Secure session</strong><span>{user?.username}</span></div>
        </div>
      </aside>
      <div className="app-main">
        <header className="topbar">
          <div><span className="live-dot" />AWS development environment</div>
          <button className="button button-quiet" onClick={signOut}>Sign out</button>
        </header>
        <main className="page"><Outlet /></main>
      </div>
    </div>
  );
}
