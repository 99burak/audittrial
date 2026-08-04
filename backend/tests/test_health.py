from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.main import app

client = TestClient(app)


def test_health_reports_api_is_running() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_reports_database_is_ready(monkeypatch) -> None:
    monkeypatch.setattr("app.main.check_database_connection", lambda: None)

    response = client.get("/api/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_readiness_hides_database_error_details(monkeypatch) -> None:
    def fail_connection() -> None:
        raise OperationalError("SELECT 1", {}, Exception("database details"))

    monkeypatch.setattr("app.main.check_database_connection", fail_connection)

    response = client.get("/api/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert "database details" not in response.text

