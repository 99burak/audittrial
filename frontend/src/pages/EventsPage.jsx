import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getEvents } from "../api.js";

const dateFormatter = new Intl.DateTimeFormat("en", {
  dateStyle: "medium",
  timeStyle: "medium",
});

const PAGE_SIZE = 20;
const EMPTY_FILTERS = {
  applicationId: "",
  actorId: "",
  action: "",
  resourceType: "",
  dateFrom: "",
  dateTo: "",
};

function formatDate(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : dateFormatter.format(date);
}

function EventsPage() {
  const [eventPage, setEventPage] = useState(null);
  const [page, setPage] = useState(1);
  const [filterForm, setFilterForm] = useState(EMPTY_FILTERS);
  const [appliedFilters, setAppliedFilters] = useState(EMPTY_FILTERS);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let cancelled = false;

    setIsLoading(true);
    setError("");

    getEvents({ page, pageSize: PAGE_SIZE, filters: appliedFilters })
      .then((data) => {
        if (!cancelled) {
          setEventPage(data);
        }
      })
      .catch((requestError) => {
        if (!cancelled) {
          setError(requestError.message ?? "Unable to load audit events.");
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
  }, [appliedFilters, page, refreshKey]);

  function handleFilterChange(event) {
    const { name, value } = event.target;
    setFilterForm((current) => ({ ...current, [name]: value }));
  }

  function handleFilterSubmit(event) {
    event.preventDefault();
    setPage(1);
    setAppliedFilters({
      ...filterForm,
      dateFrom: filterForm.dateFrom
        ? new Date(filterForm.dateFrom).toISOString()
        : "",
      dateTo: filterForm.dateTo
        ? new Date(filterForm.dateTo).toISOString()
        : "",
    });
  }

  function clearFilters() {
    setFilterForm(EMPTY_FILTERS);
    setPage(1);
    setAppliedFilters(EMPTY_FILTERS);
  }

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

      <form className="panel filter-panel" onSubmit={handleFilterSubmit}>
        <div className="filter-grid">
          <label>
            Application ID
            <input
              min="1"
              name="applicationId"
              placeholder="e.g. 1"
              type="number"
              value={filterForm.applicationId}
              onChange={handleFilterChange}
            />
          </label>
          <label>
            Actor ID
            <input
              name="actorId"
              placeholder="e.g. user-42"
              type="text"
              value={filterForm.actorId}
              onChange={handleFilterChange}
            />
          </label>
          <label>
            Action
            <input
              name="action"
              placeholder="e.g. user.login"
              type="text"
              value={filterForm.action}
              onChange={handleFilterChange}
            />
          </label>
          <label>
            Resource type
            <input
              name="resourceType"
              placeholder="e.g. user"
              type="text"
              value={filterForm.resourceType}
              onChange={handleFilterChange}
            />
          </label>
          <label>
            From
            <input
              name="dateFrom"
              type="datetime-local"
              value={filterForm.dateFrom}
              onChange={handleFilterChange}
            />
          </label>
          <label>
            To
            <input
              name="dateTo"
              type="datetime-local"
              value={filterForm.dateTo}
              onChange={handleFilterChange}
            />
          </label>
        </div>
        <div className="filter-actions">
          <button className="primary-button" type="submit">
            Apply filters
          </button>
          <button
            className="outline-button"
            type="button"
            onClick={clearFilters}
          >
            Clear filters
          </button>
        </div>
      </form>

      {isLoading && (
        <div className="panel empty-state" aria-live="polite">
          <h3>Loading audit events...</h3>
        </div>
      )}

      {!isLoading && error && (
        <div className="panel empty-state" role="alert">
          <h3>{error}</h3>
          <p>Review the filters or check the API service, then try again.</p>
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
          <h3>No matching audit events</h3>
          <p>Change the filters or wait for new events to arrive.</p>
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
