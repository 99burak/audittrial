import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getEvent } from "../api.js";

const dateFormatter = new Intl.DateTimeFormat("en", {
  dateStyle: "medium",
  timeStyle: "long",
});

function formatDate(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : dateFormatter.format(date);
}

function JsonBlock({ title, value }) {
  return (
    <article className="json-card">
      <h3>{title}</h3>
      {value ? (
        <pre>{JSON.stringify(value, null, 2)}</pre>
      ) : (
        <p className="muted">No data was provided.</p>
      )}
    </article>
  );
}

function EventDetailPage() {
  const { eventId } = useParams();
  const [event, setEvent] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let cancelled = false;

    setIsLoading(true);
    setError("");

    getEvent(eventId)
      .then((data) => {
        if (!cancelled) {
          setEvent(data);
        }
      })
      .catch((requestError) => {
        if (!cancelled) {
          setError(requestError.message ?? "Unable to load this event.");
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
  }, [eventId, refreshKey]);

  return (
    <section>
      <div className="page-heading">
        <div>
          <p className="eyebrow">EVENT DETAILS</p>
          <h2>Event #{eventId}</h2>
        </div>
        <Link className="back-link" to="/events">
          Back to events
        </Link>
      </div>

      {isLoading && (
        <div className="panel empty-state" aria-live="polite">
          <h3>Loading event details...</h3>
        </div>
      )}

      {!isLoading && error && (
        <div className="panel empty-state" role="alert">
          <h3>{error}</h3>
          <p>The event may not exist or the API may be unavailable.</p>
          <button
            className="primary-button compact-button"
            type="button"
            onClick={() => setRefreshKey((current) => current + 1)}
          >
            Try again
          </button>
        </div>
      )}

      {!isLoading && !error && event && (
        <>
          <div className="panel detail-panel">
            <dl className="detail-grid">
              <div>
                <dt>Application</dt>
                <dd>App #{event.application_id}</dd>
              </div>
              <div>
                <dt>Actor</dt>
                <dd>{event.actor_id}</dd>
              </div>
              <div>
                <dt>Action</dt>
                <dd>
                  <span className="action-badge">{event.action}</span>
                </dd>
              </div>
              <div>
                <dt>Resource type</dt>
                <dd>{event.resource_type}</dd>
              </div>
              <div>
                <dt>Resource ID</dt>
                <dd>{event.resource_id}</dd>
              </div>
              <div>
                <dt>IP address</dt>
                <dd>{event.ip_address ?? "—"}</dd>
              </div>
              <div>
                <dt>Occurred at</dt>
                <dd>{formatDate(event.occurred_at)}</dd>
              </div>
              <div>
                <dt>Received at</dt>
                <dd>{formatDate(event.received_at)}</dd>
              </div>
            </dl>
          </div>

          <div className="json-grid">
            <JsonBlock title="Old values" value={event.old_values} />
            <JsonBlock title="New values" value={event.new_values} />
            <JsonBlock title="Metadata" value={event.metadata} />
          </div>
        </>
      )}
    </section>
  );
}

export default EventDetailPage;
