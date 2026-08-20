import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { getCurrentUser, login, logout } from "./api.js";
import Layout from "./components/Layout.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import AdminPage from "./pages/AdminPage.jsx";
import EventDetailPage from "./pages/EventDetailPage.jsx";
import EventsPage from "./pages/EventsPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";

function App() {
  const [user, setUser] = useState(null);
  const [authStatus, setAuthStatus] = useState("loading");

  useEffect(() => {
    getCurrentUser()
      .then((currentUser) => setUser(currentUser))
      .catch(() => setUser(null))
      .finally(() => setAuthStatus("ready"));
  }, []);

  async function handleLogin(credentials) {
    const authenticatedUser = await login(credentials);
    setUser(authenticatedUser);
    return authenticatedUser;
  }

  async function handleLogout() {
    try {
      await logout();
    } finally {
      setUser(null);
    }
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={
          <LoginPage
            authStatus={authStatus}
            user={user}
            onLogin={handleLogin}
          />
        }
      />
      <Route
        element={
          <ProtectedRoute authStatus={authStatus} user={user}>
            <Layout user={user} onLogout={handleLogout} />
          </ProtectedRoute>
        }
      >
        <Route path="/events" element={<EventsPage />} />
        <Route path="/events/:eventId" element={<EventDetailPage />} />
        <Route
          path="/admin"
          element={
            <ProtectedRoute
              authStatus={authStatus}
              user={user}
              requiredRole="admin"
            >
              <AdminPage />
            </ProtectedRoute>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/events" replace />} />
    </Routes>
  );
}

export default App;
