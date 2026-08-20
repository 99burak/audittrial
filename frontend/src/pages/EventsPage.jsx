function EventsPage() {
  return (
    <section>
      <div className="page-heading">
        <div>
          <p className="eyebrow">AUDIT EVENTS</p>
          <h2>Activity records</h2>
        </div>
        <span className="status-badge">Skeleton ready</span>
      </div>

      <div className="panel empty-state">
        <h3>The event list will appear here</h3>
        <p>
          Filters, pagination, and backend data will be connected in the next
          stage.
        </p>
      </div>
    </section>
  );
}

export default EventsPage;
