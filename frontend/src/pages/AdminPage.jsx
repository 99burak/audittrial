function AdminPage() {
  return (
    <section>
      <div className="page-heading">
        <div>
          <p className="eyebrow">ADMINISTRATION</p>
          <h2>Admin tools</h2>
        </div>
      </div>

      <div className="card-grid">
        <article className="panel">
          <h3>Users</h3>
          <p>Panel users and roles will be managed here.</p>
        </article>
        <article className="panel">
          <h3>Applications</h3>
          <p>Applications that send events will be managed here.</p>
        </article>
        <article className="panel">
          <h3>API keys</h3>
          <p>Key creation and revocation will be managed here.</p>
        </article>
      </div>
    </section>
  );
}

export default AdminPage;
