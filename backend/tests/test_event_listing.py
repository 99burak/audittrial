from collections.abc import Generator
from datetime import UTC, datetime
from ipaddress import ip_address

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_db
from app.core.security import hash_password
from app.main import app
from app.models import AuditEvent, User

TEST_PASSWORD = "a-secure-test-password"


class FakeScalarResult:
    def __init__(self, events: list[AuditEvent]) -> None:
        self.events = events

    def all(self) -> list[AuditEvent]:
        return self.events


class FakeSession:
    def __init__(
        self,
        current_user: User,
        events: list[AuditEvent],
        total: int,
    ) -> None:
        self.current_user = current_user
        self.events = events
        self.total = total
        self.scalar_call_count = 0
        self.scalar_statements = []
        self.scalars_statement = None

    def scalar(self, statement):
        self.scalar_call_count += 1
        self.scalar_statements.append(statement)
        if self.scalar_call_count == 1:
            return self.current_user
        return self.total

    def get(self, model, object_id: int) -> User | None:
        if model is User and self.current_user.id == object_id:
            return self.current_user
        return None

    def scalars(self, statement) -> FakeScalarResult:
        self.scalars_statement = statement
        return FakeScalarResult(self.events)


def make_user(role: str) -> User:
    user = User(
        username=role,
        password_hash=hash_password(TEST_PASSWORD),
        role=role,
        is_active=True,
    )
    user.id = 1
    return user


def make_event(event_id: int) -> AuditEvent:
    now = datetime.now(UTC)
    event = AuditEvent(
        application_id=10,
        actor_id=f"user-{event_id}",
        action="invoice.updated",
        resource_type="invoice",
        resource_id=f"inv-{event_id}",
        old_values=None,
        new_values={"status": "paid"},
        ip_address=ip_address("192.0.2.10"),
        event_metadata={"source": "test"},
        occurred_at=now,
    )
    event.id = event_id
    event.received_at = now
    return event


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def use_fake_session(
    current_user: User,
    events: list[AuditEvent],
    total: int | None = None,
) -> FakeSession:
    fake_session = FakeSession(
        current_user,
        events,
        len(events) if total is None else total,
    )

    def override_get_db():
        yield fake_session

    app.dependency_overrides[get_db] = override_get_db
    return fake_session


def login(client: TestClient, role: str) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": role, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200


def test_event_list_requires_authentication(client: TestClient) -> None:
    use_fake_session(make_user("viewer"), [])

    response = client.get("/api/events")

    assert response.status_code == 401


@pytest.mark.parametrize("role", ["admin", "viewer"])
def test_panel_roles_can_list_events(client: TestClient, role: str) -> None:
    event = make_event(1)
    use_fake_session(make_user(role), [event])
    login(client, role)

    response = client.get("/api/events")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == 1
    assert response.json()["items"][0]["ip_address"] == "192.0.2.10"


def test_event_list_returns_pagination_metadata(client: TestClient) -> None:
    event = make_event(2)
    use_fake_session(make_user("viewer"), [event], total=3)
    login(client, "viewer")

    response = client.get("/api/events?page=2&page_size=1")

    assert response.status_code == 200
    assert response.json()["page"] == 2
    assert response.json()["page_size"] == 1
    assert response.json()["total"] == 3
    assert [item["id"] for item in response.json()["items"]] == [2]


@pytest.mark.parametrize(
    "query",
    ["page=0", "page_size=0", "page_size=101"],
)
def test_event_list_rejects_invalid_pagination(
    client: TestClient,
    query: str,
) -> None:
    use_fake_session(make_user("viewer"), [])
    login(client, "viewer")

    response = client.get(f"/api/events?{query}")

    assert response.status_code == 422


def test_event_list_applies_all_filters(client: TestClient) -> None:
    session = use_fake_session(make_user("viewer"), [make_event(1)], total=1)
    login(client, "viewer")

    response = client.get(
        "/api/events",
        params={
            "application_id": 10,
            "actor_id": " user-42 ",
            "action": "invoice.updated",
            "resource_type": "invoice",
            "date_from": "2026-08-17T00:00:00+03:00",
            "date_to": "2026-08-18T23:59:59+03:00",
        },
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    count_statement = session.scalar_statements[-1]
    assert len(count_statement._where_criteria) == 6
    assert session.scalars_statement is not None
    assert len(session.scalars_statement._where_criteria) == 6


def test_event_list_rejects_reversed_date_range(client: TestClient) -> None:
    use_fake_session(make_user("viewer"), [])
    login(client, "viewer")

    response = client.get(
        "/api/events",
        params={
            "date_from": "2026-08-19T00:00:00+03:00",
            "date_to": "2026-08-18T00:00:00+03:00",
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "date_from cannot be after date_to"}


@pytest.mark.parametrize("filter_name", ["date_from", "date_to"])
def test_event_list_requires_timezone_in_date_filters(
    client: TestClient,
    filter_name: str,
) -> None:
    use_fake_session(make_user("viewer"), [])
    login(client, "viewer")

    response = client.get(
        "/api/events",
        params={filter_name: "2026-08-18T12:00:00"},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": f"{filter_name} must include a timezone"
    }
