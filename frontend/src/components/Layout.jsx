import { NavLink, Outlet } from "react-router-dom";

function Layout() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">CENTRAL AUDIT PANEL</p>
          <h1>AuditTrail</h1>
        </div>

        <nav aria-label="Main navigation">
          <NavLink to="/events">Events</NavLink>
          <NavLink to="/admin">Admin</NavLink>
        </nav>
      </header>

      <main className="page-container">
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;
