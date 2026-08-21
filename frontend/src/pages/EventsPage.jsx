import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getEvents } from "../api.js";

const dateFormatter = new Intl.DateTimeFormat("en", {
  dateStyle: "medium",
  timeStyle: "medium",
});

const PAGE_SIZE = 20;

function formatDate(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : dateFormatter.format(date);
}

function EventsPage() {
  const [eventPage, setEventPage] = useState(null);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let cancelled = false;

    setIsLoading(true);
    setError("");

    getEvents({ page, pageSize: PAGE_SIZE })
      .then((data) => {
        if (!cancelled) {
          setEventPage(data);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError("Unable to load audit events.");
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
  }, [page, refreshKey]);

  const events = eventPage?.items ?? [];
  const totalPages = Math.max(
    1,
    Math.ceil((eventPage?.total ?? 0) / PAGE_SIZE),
  );

  return (
    <section>
      <div className="page-heading">
        <div>
          <p className="eyebrow">AUDIT EVENTS</p>
          <h2>Activity records</h2>
        </div>
        {!isLoading && !error && (
          <span className="status-badge">
            {eventPage?.total ?? 0} total events
          </span>
        )}
      </div>

      {isLoading && (
        <div className="panel empty-state" aria-live="polite">
          <h3>Loading audit events...</h3>
        </div>
      )}

      {!isLoading && error && (
        <div className="panel empty-state" role="alert">
          <h3>{error}</h3>
          <p>Check the API service and try again.</p>
          <button
            className="primary-button compact-button"
            type="button"
            onClick={() => setRefreshKey((current) => current + 1)}
          >
            Try again
          </button>
        </div>
      )}

      {!isLoading && !error && events.length === 0 && (
        <div className="panel empty-state">
          <h3>No audit events yet</h3>
          <p>Events sent by your applications will appear here.</p>
        </div>
      )}

      {!isLoading && !error && events.length > 0 && (
        <div className="panel table-panel">
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Occurred</th>
                  <th>Application</th>
                  <th>Actor</th>
                  <th>Action</th>
                  <th>Resource</th>
                  <th aria-label="Event details" />
                </tr>
              </thead>
              <tbody>
                {events.map((event) => (
                  <tr key={event.id}>
                    <td className="date-cell">{formatDate(event.occurred_at)}</td>
                    <td>App #{event.application_id}</td>
                    <td>{event.actor_id}</td>
                    <td>
                      <span className="action-badge">{event.action}</span>
                    </td>
                    <td>
                      <strong>{event.resource_type}</strong>
                      <span className="resource-id">{event.resource_id}</span>
                    </td>
                    <td className="table-action">
                      <Link to={`/events/${event.id}`}>View</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pagination" aria-label="Event list pagination">
            <button
              className="pagination-button"
              type="button"
              disabled={page === 1}
              onClick={() => setPage((current) => current - 1)}
            >
              Previous
            </button>
            <span>
              Page <strong>{page}</strong> of <strong>{totalPages}</strong>
            </span>
            <button
              className="pagination-button"
              type="button"
              disabled={page >= totalPages}
              onClick={() => setPage((current) => current + 1)}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </section>
  );
}

export default EventsPage;
