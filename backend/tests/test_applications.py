from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_db
from app.core.security import hash_password
from app.main import app
from app.models import Application, User

TEST_PASSWORD = "a-secure-test-password"


class FakeScalarResult:
    def __init__(self, applications: list[Application]) -> None:
        self.applications = applications

    def all(self) -> list[Application]:
        return self.applications


class FakeSession:
    def __init__(
        self,
        current_user: User,
        applications: list[Application],
        existing_application: Application | None = None,
    ) -> None:
        self.current_user = current_user
        self.applications = applications
        self.existing_application = existing_application
        self.scalar_call_count = 0
        self.added_application: Application | None = None
        self.committed = False

    def scalar(self, statement):
        self.scalar_call_count += 1
        if self.scalar_call_count == 1:
            return self.current_user
        return self.existing_application

    def get(self, model, object_id: int) -> User | None:
        if model is User and self.current_user.id == object_id:
            return self.current_user
        return None

    def scalars(self, statement) -> FakeScalarResult:
        return FakeScalarResult(self.applications)

    def add(self, application: Application) -> None:
        self.added_application = application

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.committed = False

    def refresh(self, application: Application) -> None:
        now = datetime.now(UTC)
        application.id = 3
        application.created_at = now
        application.updated_at = now


def make_user(role: str) -> User:
    user = User(
        username=role,
        password_hash=hash_password(TEST_PASSWORD),
        role=role,
        is_active=True,
    )
    user.id = 1
    return user


def make_application(application_id: int, name: str) -> Application:
    now = datetime.now(UTC)
    application = Application(name=name, description=None, is_active=True)
    application.id = application_id
    application.created_at = now
    application.updated_at = now
    return application


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def use_fake_session(
    current_user: User,
    applications: list[Application],
    existing_application: Application | None = None,
) -> FakeSession:
    fake_session = FakeSession(
        current_user,
        applications,
        existing_application,
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


def test_application_list_requires_authentication(client: TestClient) -> None:
    admin = make_user("admin")
    use_fake_session(admin, [])

    response = client.get("/api/admin/applications")

    assert response.status_code == 401


def test_viewer_cannot_list_applications(client: TestClient) -> None:
    viewer = make_user("viewer")
    use_fake_session(viewer, [])
    login(client, "viewer")

    response = client.get("/api/admin/applications")

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin role required"}


def test_viewer_cannot_create_application(client: TestClient) -> None:
    viewer = make_user("viewer")
    session = use_fake_session(viewer, [])
    login(client, "viewer")

    response = client.post(
        "/api/admin/applications",
        json={"name": "Billing"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin role required"}
    assert session.added_application is None


def test_admin_can_list_applications(client: TestClient) -> None:
    admin = make_user("admin")
    first_application = make_application(1, "Billing")
    second_application = make_application(2, "Support")
    use_fake_session(admin, [first_application, second_application])
    login(client, "admin")

    response = client.get("/api/admin/applications")

    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["Billing", "Support"]


def test_admin_can_create_application(client: TestClient) -> None:
    admin = make_user("admin")
    session = use_fake_session(admin, [])
    login(client, "admin")

    response = client.post(
        "/api/admin/applications",
        json={"name": "  Billing  ", "description": "  Payment events  "},
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Billing"
    assert response.json()["description"] == "Payment events"
    assert response.json()["is_active"] is True
    assert session.added_application is not None
    assert session.committed is True


def test_create_application_rejects_duplicate_name(client: TestClient) -> None:
    admin = make_user("admin")
    existing_application = make_application(1, "Billing")
    session = use_fake_session(admin, [], existing_application)
    login(client, "admin")

    response = client.post(
        "/api/admin/applications",
        json={"name": "Billing"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Application name already exists"}
    assert session.added_application is None


def test_create_application_rejects_blank_name(client: TestClient) -> None:
    admin = make_user("admin")
    session = use_fake_session(admin, [])
    login(client, "admin")

    response = client.post(
        "/api/admin/applications",
        json={"name": "   "},
    )

    assert response.status_code == 422
    assert session.added_application is None
