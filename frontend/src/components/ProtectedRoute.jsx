import { Navigate, useLocation } from "react-router-dom";

function ProtectedRoute({ authStatus, user, requiredRole, children }) {
  const location = useLocation();

  if (authStatus === "loading") {
    return (
      <main className="centered-page">
        <p className="session-message">Checking your session...</p>
      </main>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requiredRole && user.role !== requiredRole) {
    return <Navigate to="/events" replace />;
  }

  return children;
}

export default ProtectedRoute;
