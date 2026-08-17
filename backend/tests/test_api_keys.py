from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_db
from app.core.security import hash_api_key, hash_password
from app.main import app
from app.models import ApiKey, Application, User

TEST_PASSWORD = "a-secure-test-password"


class FakeSession:
    def __init__(
        self,
        current_user: User,
        application: Application | None,
    ) -> None:
        self.current_user = current_user
        self.application = application
        self.added_api_key: ApiKey | None = None
        self.committed = False

    def scalar(self, statement) -> User:
        return self.current_user

    def get(self, model, object_id: int):
        if model is User and self.current_user.id == object_id:
            return self.current_user
        if (
            model is Application
            and self.application is not None
            and self.application.id == object_id
        ):
            return self.application
        return None

    def add(self, api_key: ApiKey) -> None:
        self.added_api_key = api_key

    def commit(self) -> None:
        self.committed = True

    def refresh(self, api_key: ApiKey) -> None:
        api_key.id = 1
        api_key.created_at = datetime.now(UTC)


def make_user(role: str) -> User:
    user = User(
        username=role,
        password_hash=hash_password(TEST_PASSWORD),
        role=role,
        is_active=True,
    )
    user.id = 1
    return user


def make_application() -> Application:
    application = Application(
        name="Billing",
        description=None,
        is_active=True,
    )
    application.id = 10
    return application


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def use_fake_session(
    current_user: User,
    application: Application | None,
) -> FakeSession:
    fake_session = FakeSession(current_user, application)

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


def test_create_api_key_requires_authentication(client: TestClient) -> None:
    admin = make_user("admin")
    use_fake_session(admin, make_application())

    response = client.post(
        "/api/admin/applications/10/api-keys",
        json={"name": "Production"},
    )

    assert response.status_code == 401


def test_viewer_cannot_create_api_key(client: TestClient) -> None:
    viewer = make_user("viewer")
    session = use_fake_session(viewer, make_application())
    login(client, "viewer")

    response = client.post(
        "/api/admin/applications/10/api-keys",
        json={"name": "Production"},
    )

    assert response.status_code == 403
    assert session.added_api_key is None


def test_create_api_key_returns_404_for_unknown_application(
    client: TestClient,
) -> None:
    admin = make_user("admin")
    session = use_fake_session(admin, None)
    login(client, "admin")

    response = client.post(
        "/api/admin/applications/999/api-keys",
        json={"name": "Production"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Application not found"}
    assert session.added_api_key is None


def test_admin_can_create_api_key_without_storing_plain_text(
    client: TestClient,
) -> None:
    admin = make_user("admin")
    application = make_application()
    session = use_fake_session(admin, application)
    login(client, "admin")

    response = client.post(
        "/api/admin/applications/10/api-keys",
        json={"name": "  Production  "},
    )

    assert response.status_code == 201
    response_data = response.json()
    plain_api_key = response_data["api_key"]
    assert response_data["application_id"] == 10
    assert response_data["name"] == "Production"
    assert response_data["key_prefix"] == plain_api_key[:12]
    assert plain_api_key.startswith("at_")
    assert session.added_api_key is not None
    assert session.added_api_key.key_hash == hash_api_key(plain_api_key)
    assert session.added_api_key.key_hash != plain_api_key
    assert session.added_api_key.created_by_user_id == admin.id
    assert session.committed is True


def test_create_api_key_rejects_blank_name(client: TestClient) -> None:
    admin = make_user("admin")
    session = use_fake_session(admin, make_application())
    login(client, "admin")

    response = client.post(
        "/api/admin/applications/10/api-keys",
        json={"name": "   "},
    )

    assert response.status_code == 422
    assert session.added_api_key is None
