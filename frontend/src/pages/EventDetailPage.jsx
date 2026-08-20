import { useParams } from "react-router-dom";

function EventDetailPage() {
  const { eventId } = useParams();

  return (
    <section>
      <div className="page-heading">
        <div>
          <p className="eyebrow">EVENT DETAILS</p>
          <h2>Event #{eventId}</h2>
        </div>
      </div>

      <div className="panel empty-state">
        <h3>Event details will appear here</h3>
        <p>Old and new JSON values will be displayed in a later stage.</p>
      </div>
    </section>
  );
}

export default EventDetailPage;
