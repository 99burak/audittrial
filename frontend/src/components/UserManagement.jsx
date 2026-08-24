import { useEffect, useState } from "react";

import { createUser, getUsers, updateUserStatus } from "../api.js";

function UserManagement() {
  const [users, setUsers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("viewer");
  const [isCreating, setIsCreating] = useState(false);
  const [createError, setCreateError] = useState("");
  const [statusError, setStatusError] = useState("");
  const [updatingUserId, setUpdatingUserId] = useState(null);

  useEffect(() => {
    let cancelled = false;

    getUsers()
      .then((data) => {
        if (!cancelled) {
          setUsers(data);
        }
      })
      .catch((requestError) => {
        if (!cancelled) {
          setLoadError(requestError.message ?? "Unable to load users.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  async function handleCreateUser(event) {
    event.preventDefault();
    setIsCreating(true);
    setCreateError("");

    try {
      const user = await createUser({ username, password, role });
      setUsers((current) => [...current, user]);
      setUsername("");
      setPassword("");
      setRole("viewer");
    } catch (requestError) {
      setCreateError(requestError.message ?? "Unable to create the user.");
    } finally {
      setIsCreating(false);
    }
  }

  async function handleStatusChange(user) {
    setUpdatingUserId(user.id);
    setStatusError("");

    try {
      const updatedUser = await updateUserStatus(user.id, !user.is_active);
      setUsers((current) =>
        current.map((item) =>
          item.id === updatedUser.id ? updatedUser : item,
        ),
      );
    } catch (requestError) {
      setStatusError(requestError.message ?? "Unable to update the user.");
    } finally {
      setUpdatingUserId(null);
    }
  }

  return (
    <section className="user-management">
      <div className="section-title">
        <p className="eyebrow">PANEL USERS</p>
        <h3>User management</h3>
      </div>

      <div className="admin-layout">
        <form className="panel admin-form" onSubmit={handleCreateUser}>
          <div>
            <p className="eyebrow">NEW USER</p>
            <h3>Create a panel user</h3>
            <p>Viewers can only view events. Admins can manage the system.</p>
          </div>

          <label>
            Username
            <input
              autoComplete="off"
              maxLength="100"
              name="username"
              required
              type="text"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
            />
          </label>

          <label>
            Password
            <input
              autoComplete="new-password"
              maxLength="1024"
              minLength="12"
              name="password"
              required
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            <span className="field-hint">At least 12 characters.</span>
          </label>

          <label>
            Role
            <select
              name="role"
              value={role}
              onChange={(event) => setRole(event.target.value)}
            >
              <option value="viewer">Viewer</option>
              <option value="admin">Admin</option>
            </select>
          </label>

          {createError && (
            <p className="error-message" role="alert">
              {createError}
            </p>
          )}

          <button
            className="primary-button"
            disabled={isCreating}
            type="submit"
          >
            {isCreating ? "Creating..." : "Create user"}
          </button>
        </form>

        <div className="panel admin-list-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">USERS</p>
              <h3>Panel access</h3>
            </div>
            {!isLoading && !loadError && (
              <span className="status-badge">{users.length} total</span>
            )}
          </div>

          {statusError && (
            <p className="error-message admin-action-message" role="alert">
              {statusError}
            </p>
          )}

          {isLoading && <p aria-live="polite">Loading users...</p>}

          {!isLoading && loadError && (
            <p className="error-message" role="alert">
              {loadError}
            </p>
          )}

          {!isLoading && !loadError && users.length === 0 && (
            <p>No panel users exist yet.</p>
          )}

          {!isLoading && !loadError && users.length > 0 && (
            <div className="user-list">
              {users.map((user) => (
                <article className="user-item" key={user.id}>
                  <div>
                    <div className="application-title">
                      <h4>{user.username}</h4>
                      <span className="role-badge">{user.role}</span>
                      <span
                        className={
                          user.is_active
                            ? "state-badge active-state"
                            : "state-badge inactive-state"
                        }
                      >
                        {user.is_active ? "Active" : "Inactive"}
                      </span>
                    </div>
                    <p>User ID {user.id}</p>
                  </div>
                  <button
                    className={
                      user.is_active
                        ? "danger-button small-button"
                        : "outline-button small-button"
                    }
                    disabled={updatingUserId === user.id}
                    type="button"
                    onClick={() => handleStatusChange(user)}
                  >
                    {updatingUserId === user.id
                      ? "Updating..."
                      : user.is_active
                        ? "Deactivate"
                        : "Activate"}
                  </button>
                </article>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

export default UserManagement;
