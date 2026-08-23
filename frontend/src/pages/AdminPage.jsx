import { useEffect, useState } from "react";

import { createApplication, getApplications } from "../api.js";

const dateFormatter = new Intl.DateTimeFormat("en", { dateStyle: "medium" });

function formatDate(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : dateFormatter.format(date);
}

function AdminPage() {
  const [applications, setApplications] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [createError, setCreateError] = useState("");

  useEffect(() => {
    let cancelled = false;

    getApplications()
      .then((data) => {
        if (!cancelled) {
          setApplications(data);
        }
      })
      .catch((requestError) => {
        if (!cancelled) {
          setLoadError(
            requestError.message ?? "Unable to load applications.",
          );
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

  async function handleCreateApplication(event) {
    event.preventDefault();
    setIsCreating(true);
    setCreateError("");

    try {
      const application = await createApplication({
        name,
        description: description || null,
      });
      setApplications((current) => [...current, application]);
      setName("");
      setDescription("");
    } catch (requestError) {
      setCreateError(
        requestError.message ?? "Unable to create the application.",
      );
    } finally {
      setIsCreating(false);
    }
  }

  return (
    <section>
      <div className="page-heading">
        <div>
          <p className="eyebrow">ADMINISTRATION</p>
          <h2>Admin tools</h2>
        </div>
      </div>

      <div className="admin-layout">
        <form className="panel admin-form" onSubmit={handleCreateApplication}>
          <div>
            <p className="eyebrow">NEW APPLICATION</p>
            <h3>Create an application</h3>
            <p>Applications represent the systems that send audit events.</p>
          </div>

          <label>
            Name
            <input
              maxLength="150"
              name="name"
              required
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </label>

          <label>
            Description <span className="muted">(optional)</span>
            <textarea
              maxLength="2000"
              name="description"
              rows="4"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
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
            {isCreating ? "Creating..." : "Create application"}
          </button>
        </form>

        <div className="panel admin-list-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">APPLICATIONS</p>
              <h3>Event sources</h3>
            </div>
            {!isLoading && !loadError && (
              <span className="status-badge">
                {applications.length} total
              </span>
            )}
          </div>

          {isLoading && <p aria-live="polite">Loading applications...</p>}

          {!isLoading && loadError && (
            <p className="error-message" role="alert">
              {loadError}
            </p>
          )}

          {!isLoading && !loadError && applications.length === 0 && (
            <p>No applications have been created yet.</p>
          )}

          {!isLoading && !loadError && applications.length > 0 && (
            <div className="application-list">
              {applications.map((application) => (
                <article className="application-item" key={application.id}>
                  <div>
                    <div className="application-title">
                      <h4>{application.name}</h4>
                      <span
                        className={
                          application.is_active
                            ? "state-badge active-state"
                            : "state-badge inactive-state"
                        }
                      >
                        {application.is_active ? "Active" : "Inactive"}
                      </span>
                    </div>
                    <p>{application.description || "No description"}</p>
                  </div>
                  <span className="application-meta">
                    ID {application.id} · Created {formatDate(application.created_at)}
                  </span>
                </article>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="card-grid admin-placeholders">
        <article className="panel">
          <h3>API keys</h3>
          <p>API key management is the next development step.</p>
        </article>
        <article className="panel">
          <h3>Users</h3>
          <p>User management will be added after API keys.</p>
        </article>
      </div>
    </section>
  );
}

export default AdminPage;
