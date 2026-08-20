import { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

function LoginPage({ authStatus, user, onLogin }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (authStatus === "loading") {
    return (
      <main className="centered-page">
        <p className="session-message">Checking your session...</p>
      </main>
    );
  }

  if (authStatus === "ready" && user) {
    return <Navigate to="/events" replace />;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      await onLogin({ username, password });
      const destination = location.state?.from?.pathname ?? "/events";
      navigate(destination, { replace: true });
    } catch (requestError) {
      if (requestError.status === 401) {
        setError("Invalid username or password.");
      } else {
        setError("Unable to sign in. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="centered-page">
      <section className="panel login-panel">
        <p className="eyebrow">AUDITTRAIL</p>
        <h1>Sign in to the panel</h1>
        <p className="muted">Use your AuditTrail panel account to continue.</p>

        <form className="login-form" onSubmit={handleSubmit}>
          <label htmlFor="username">Username</label>
          <input
            id="username"
            name="username"
            type="text"
            autoComplete="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            disabled={isSubmitting}
            required
            autoFocus
          />

          <label htmlFor="password">Password</label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            disabled={isSubmitting}
            required
          />

          {error && (
            <p className="error-message" role="alert">
              {error}
            </p>
          )}

          <button className="primary-button" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
}

export default LoginPage;
