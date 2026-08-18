from collections.abc import Generator
from datetime import UTC, datetime
from ipaddress import ip_address

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_db
from app.core.security import hash_api_key
from app.main import app
from app.models import ApiKey, Application, AuditEvent

PLAIN_API_KEY = "at_a-secure-test-api-key"


class FakeSession:
    def __init__(
        self,
        api_key: ApiKey | None,
        application: Application | None,
    ) -> None:
        self.api_key = api_key
        self.application = application
        self.added_event: AuditEvent | None = None
        self.committed = False

    def scalar(self, statement) -> ApiKey | None:
        return self.api_key

    def get(self, model, object_id: int) -> Application | None:
        if (
            model is Application
            and self.application is not None
            and self.application.id == object_id
        ):
            return self.application
        return None

    def add(self, event: AuditEvent) -> None:
        self.added_event = event

    def commit(self) -> None:
        self.committed = True

    def refresh(self, event: AuditEvent) -> None:
        event.id = 100
        if event.ip_address is not None:
            event.ip_address = ip_address(event.ip_address)
        event.received_at = datetime.now(UTC)


def make_application(is_active: bool = True) -> Application:
    application = Application(
        name="Billing",
        description=None,
        is_active=is_active,
    )
    application.id = 10
    return application


def make_api_key(revoked: bool = False) -> ApiKey:
    api_key = ApiKey(
        application_id=10,
        name="Production",
        key_prefix=PLAIN_API_KEY[:12],
        key_hash=hash_api_key(PLAIN_API_KEY),
        created_by_user_id=1,
        revoked_at=datetime.now(UTC) if revoked else None,
    )
    api_key.id = 1
    api_key.last_used_at = None
    return api_key


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def use_fake_session(
    api_key: ApiKey | None,
    application: Application | None,
) -> FakeSession:
    fake_session = FakeSession(api_key, application)

    def override_get_db():
        yield fake_session

    app.dependency_overrides[get_db] = override_get_db
    return fake_session


def valid_event_data() -> dict:
    return {
        "actor_id": "user-42",
        "action": "invoice.updated",
        "resource_type": "invoice",
        "resource_id": "inv-100",
        "old_values": {"status": "draft"},
        "new_values": {"status": "paid"},
        "ip_address": "192.0.2.10",
        "metadata": {"source": "billing-worker"},
        "occurred_at": "2026-08-17T10:30:00+03:00",
    }


def post_event(client: TestClient, api_key: str | None = PLAIN_API_KEY):
    headers = {"X-API-Key": api_key} if api_key is not None else {}
    return client.post("/api/events", json=valid_event_data(), headers=headers)


def test_event_requires_api_key(client: TestClient) -> None:
    session = use_fake_session(None, None)

    response = post_event(client, api_key=None)

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid API key"}
    assert session.added_event is None


def test_event_rejects_invalid_api_key(client: TestClient) -> None:
    session = use_fake_session(None, None)

    response = post_event(client, api_key="at_invalid")

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid API key"}
    assert session.added_event is None


def test_event_rejects_revoked_api_key(client: TestClient) -> None:
    session = use_fake_session(make_api_key(revoked=True), make_application())

    response = post_event(client)

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid API key"}
    assert session.added_event is None


def test_event_rejects_api_key_for_inactive_application(
    client: TestClient,
) -> None:
    session = use_fake_session(make_api_key(), make_application(is_active=False))

    response = post_event(client)

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid API key"}
    assert session.added_event is None


def test_valid_api_key_can_create_event(client: TestClient) -> None:
    api_key = make_api_key()
    session = use_fake_session(api_key, make_application())

    response = post_event(client)

    assert response.status_code == 201
    response_data = response.json()
    assert response_data["id"] == 100
    assert response_data["application_id"] == 10
    assert response_data["actor_id"] == "user-42"
    assert response_data["metadata"] == {"source": "billing-worker"}
    assert response_data["received_at"] is not None
    assert "api_key" not in response.text
    assert session.added_event is not None
    assert session.added_event.application_id == 10
    assert str(session.added_event.ip_address) == "192.0.2.10"
    assert session.added_event.event_metadata == {"source": "billing-worker"}
    assert api_key.last_used_at is not None
    assert session.committed is True


def test_event_rejects_blank_required_text(client: TestClient) -> None:
    session = use_fake_session(make_api_key(), make_application())
    event_data = valid_event_data()
    event_data["action"] = "   "

    response = client.post(
        "/api/events",
        json=event_data,
        headers={"X-API-Key": PLAIN_API_KEY},
    )

    assert response.status_code == 422
    assert session.added_event is None


def test_event_rejects_occurred_at_without_timezone(client: TestClient) -> None:
    session = use_fake_session(make_api_key(), make_application())
    event_data = valid_event_data()
    event_data["occurred_at"] = "2026-08-17T10:30:00"

    response = client.post(
        "/api/events",
        json=event_data,
        headers={"X-API-Key": PLAIN_API_KEY},
    )

    assert response.status_code == 422
    assert session.added_event is None
