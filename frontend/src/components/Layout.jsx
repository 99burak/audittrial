import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

function Layout({ user, onLogout }) {
  const navigate = useNavigate();
  const [isSigningOut, setIsSigningOut] = useState(false);

  async function handleSignOut() {
    setIsSigningOut(true);
    try {
      await onLogout();
    } finally {
      navigate("/login", { replace: true });
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">CENTRAL AUDIT PANEL</p>
          <h1>AuditTrail</h1>
        </div>

        <div className="topbar-actions">
          <nav aria-label="Main navigation">
            <NavLink to="/events">Events</NavLink>
            {user.role === "admin" && <NavLink to="/admin">Admin</NavLink>}
          </nav>

          <div className="user-menu">
            <span>
              {user.username} · {user.role}
            </span>
            <button
              className="secondary-button"
              type="button"
              onClick={handleSignOut}
              disabled={isSigningOut}
            >
              {isSigningOut ? "Signing out..." : "Sign out"}
            </button>
          </div>
        </div>
      </header>

      <main className="page-container">
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;
