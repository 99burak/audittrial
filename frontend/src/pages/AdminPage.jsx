import { useEffect, useState } from "react";

import {
  createApiKey,
  createApplication,
  getApiKeys,
  getApplications,
} from "../api.js";

const dateFormatter = new Intl.DateTimeFormat("en", { dateStyle: "medium" });

function formatDate(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : dateFormatter.format(date);
}

function AdminPage() {
  const [applications, setApplications] = useState([]);
  const [selectedApplicationId, setSelectedApplicationId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [createError, setCreateError] = useState("");
  const [apiKeys, setApiKeys] = useState([]);
  const [areKeysLoading, setAreKeysLoading] = useState(false);
  const [keysError, setKeysError] = useState("");
  const [keyName, setKeyName] = useState("");
  const [isKeyCreating, setIsKeyCreating] = useState(false);
  const [keyCreateError, setKeyCreateError] = useState("");
  const [createdApiKey, setCreatedApiKey] = useState(null);
  const [copyStatus, setCopyStatus] = useState("");

  useEffect(() => {
    let cancelled = false;

    getApplications()
      .then((data) => {
        if (!cancelled) {
          setApplications(data);
          setSelectedApplicationId(data[0]?.id ?? null);
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

  useEffect(() => {
    if (selectedApplicationId === null) {
      setApiKeys([]);
      return undefined;
    }

    let cancelled = false;
    setAreKeysLoading(true);
    setKeysError("");
    setKeyName("");
    setKeyCreateError("");
    setCreatedApiKey(null);
    setCopyStatus("");

    getApiKeys(selectedApplicationId)
      .then((data) => {
        if (!cancelled) {
          setApiKeys(data);
        }
      })
      .catch((requestError) => {
        if (!cancelled) {
          setKeysError(requestError.message ?? "Unable to load API keys.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setAreKeysLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedApplicationId]);

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
      setSelectedApplicationId((current) => current ?? application.id);
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

  async function handleCreateApiKey(event) {
    event.preventDefault();
    setIsKeyCreating(true);
    setKeyCreateError("");
    setCreatedApiKey(null);
    setCopyStatus("");

    try {
      const createdKey = await createApiKey(selectedApplicationId, {
        name: keyName,
      });
      setApiKeys((current) => [
        ...current,
        {
          id: createdKey.id,
          application_id: createdKey.application_id,
          name: createdKey.name,
          key_prefix: createdKey.key_prefix,
          created_at: createdKey.created_at,
          last_used_at: null,
          revoked_at: null,
        },
      ]);
      setCreatedApiKey(createdKey);
      setKeyName("");
    } catch (requestError) {
      setKeyCreateError(
        requestError.message ?? "Unable to create the API key.",
      );
    } finally {
      setIsKeyCreating(false);
    }
  }

  async function copyCreatedApiKey() {
    try {
      await navigator.clipboard.writeText(createdApiKey.api_key);
      setCopyStatus("Copied to clipboard.");
    } catch {
      setCopyStatus("Copy failed. Select the key and copy it manually.");
    }
  }

  const selectedApplication = applications.find(
    (application) => application.id === selectedApplicationId,
  );

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
                <article
                  className={`application-item ${
                    application.id === selectedApplicationId
                      ? "selected-application"
                      : ""
                  }`}
                  key={application.id}
                >
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
                  <div className="application-actions">
                    <span className="application-meta">
                      ID {application.id} · Created{" "}
                      {formatDate(application.created_at)}
                    </span>
                    <button
                      aria-pressed={application.id === selectedApplicationId}
                      className="outline-button small-button"
                      type="button"
                      onClick={() => setSelectedApplicationId(application.id)}
                    >
                      {application.id === selectedApplicationId
                        ? "Selected"
                        : "View keys"}
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      </div>

      <section className="panel key-panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">API KEYS</p>
            <h3>
              {selectedApplication
                ? `${selectedApplication.name} keys`
                : "Select an application"}
            </h3>
          </div>
          {selectedApplication && !areKeysLoading && !keysError && (
            <span className="status-badge">{apiKeys.length} total</span>
          )}
        </div>

        {selectedApplication && (
          <form className="key-create-form" onSubmit={handleCreateApiKey}>
            <label>
              New key name
              <input
                maxLength="100"
                name="keyName"
                placeholder="e.g. Production server"
                required
                type="text"
                value={keyName}
                onChange={(event) => setKeyName(event.target.value)}
              />
            </label>
            <button
              className="primary-button"
              disabled={isKeyCreating}
              type="submit"
            >
              {isKeyCreating ? "Creating..." : "Create API key"}
            </button>
          </form>
        )}

        {keyCreateError && (
          <p className="error-message key-message" role="alert">
            {keyCreateError}
          </p>
        )}

        {createdApiKey && (
          <div className="created-key" role="status">
            <div>
              <h4>Copy this API key now</h4>
              <p>
                This is the only time the complete key will be displayed.
              </p>
            </div>
            <div className="secret-row">
              <input
                aria-label="New API key"
                readOnly
                type="text"
                value={createdApiKey.api_key}
                onFocus={(event) => event.target.select()}
              />
              <button
                className="secondary-button"
                type="button"
                onClick={copyCreatedApiKey}
              >
                Copy
              </button>
              <button
                className="outline-button"
                type="button"
                onClick={() => setCreatedApiKey(null)}
              >
                Dismiss
              </button>
            </div>
            {copyStatus && <p className="copy-status">{copyStatus}</p>}
          </div>
        )}

        {!selectedApplication && (
          <p>Create or select an application to view its API keys.</p>
        )}

        {selectedApplication && areKeysLoading && (
          <p aria-live="polite">Loading API keys...</p>
        )}

        {selectedApplication && !areKeysLoading && keysError && (
          <p className="error-message" role="alert">
            {keysError}
          </p>
        )}

        {selectedApplication &&
          !areKeysLoading &&
          !keysError &&
          apiKeys.length === 0 && (
            <p>No API keys exist for this application yet.</p>
          )}

        {selectedApplication &&
          !areKeysLoading &&
          !keysError &&
          apiKeys.length > 0 && (
            <div className="key-list">
              {apiKeys.map((apiKey) => (
                <article className="key-item" key={apiKey.id}>
                  <div>
                    <div className="application-title">
                      <h4>{apiKey.name}</h4>
                      <span
                        className={
                          apiKey.revoked_at
                            ? "state-badge inactive-state"
                            : "state-badge active-state"
                        }
                      >
                        {apiKey.revoked_at ? "Revoked" : "Active"}
                      </span>
                    </div>
                    <code>{apiKey.key_prefix}...</code>
                  </div>
                  <div className="key-dates">
                    <span>Created {formatDate(apiKey.created_at)}</span>
                    <span>
                      Last used{" "}
                      {apiKey.last_used_at
                        ? formatDate(apiKey.last_used_at)
                        : "Never"}
                    </span>
                  </div>
                </article>
              ))}
            </div>
          )}
      </section>

      <div className="card-grid admin-placeholders users-placeholder">
        <article className="panel">
          <h3>Users</h3>
          <p>User management will be added after API keys.</p>
        </article>
      </div>
    </section>
  );
}

export default AdminPage;
