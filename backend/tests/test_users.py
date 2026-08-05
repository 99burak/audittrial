from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_db
from app.core.security import hash_password, verify_password
from app.main import app
from app.models import User

TEST_PASSWORD = "a-secure-test-password"


class FakeScalarResult:
    def __init__(self, users: list[User]) -> None:
        self.users = users

    def all(self) -> list[User]:
        return self.users


class FakeSession:
    def __init__(
        self,
        current_user: User,
        users: list[User],
        next_scalar_result=None,
    ) -> None:
        self.current_user = current_user
        self.users = users
        self.next_scalar_result = next_scalar_result
        self.scalar_call_count = 0
        self.added_user: User | None = None
        self.committed = False
        self.rolled_back = False

    def scalar(self, statement):
        self.scalar_call_count += 1
        if self.scalar_call_count == 1:
            return self.current_user
        return self.next_scalar_result

    def get(self, model, object_id: int) -> User | None:
        for user in self.users:
            if user.id == object_id:
                return user
        return None

    def scalars(self, statement) -> FakeScalarResult:
        return FakeScalarResult(self.users)

    def add(self, user: User) -> None:
        self.added_user = user

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def refresh(self, user: User) -> None:
        user.id = 3


def make_user(user_id: int, username: str, role: str) -> User:
    user = User(
        username=username,
        password_hash=hash_password(TEST_PASSWORD),
        role=role,
        is_active=True,
    )
    user.id = user_id
    return user


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def use_fake_session(
    current_user: User,
    users: list[User],
    next_scalar_result=None,
) -> FakeSession:
    fake_session = FakeSession(current_user, users, next_scalar_result)

    def override_get_db():
        yield fake_session

    app.dependency_overrides[get_db] = override_get_db
    return fake_session


def login(client: TestClient, username: str) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200


def test_user_list_requires_authentication(client: TestClient) -> None:
    admin = make_user(1, "admin", "admin")
    use_fake_session(admin, [admin])

    response = client.get("/api/admin/users")

    assert response.status_code == 401


def test_viewer_cannot_list_users(client: TestClient) -> None:
    viewer = make_user(2, "viewer", "viewer")
    use_fake_session(viewer, [viewer])
    login(client, "viewer")

    response = client.get("/api/admin/users")

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin role required"}


def test_admin_can_list_users_without_password_hashes(client: TestClient) -> None:
    admin = make_user(1, "admin", "admin")
    viewer = make_user(2, "viewer", "viewer")
    use_fake_session(admin, [admin, viewer])
    login(client, "admin")

    response = client.get("/api/admin/users")

    assert response.status_code == 200
    assert [user["username"] for user in response.json()] == ["admin", "viewer"]
    assert "password_hash" not in response.text


def test_admin_can_create_viewer_with_hashed_password(client: TestClient) -> None:
    admin = make_user(1, "admin", "admin")
    session = use_fake_session(admin, [admin])
    login(client, "admin")

    response = client.post(
        "/api/admin/users",
        json={
            "username": "  NewViewer  ",
            "password": "a-secure-viewer-password",
            "role": "viewer",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 3,
        "username": "newviewer",
        "role": "viewer",
        "is_active": True,
    }
    assert session.added_user is not None
    assert session.added_user.password_hash != "a-secure-viewer-password"
    assert (
        verify_password(
            "a-secure-viewer-password",
            session.added_user.password_hash,
        )
        is True
    )
    assert session.committed is True
    assert "password_hash" not in response.text
    assert "a-secure-viewer-password" not in response.text


def test_create_user_rejects_duplicate_username(client: TestClient) -> None:
    admin = make_user(1, "admin", "admin")
    session = use_fake_session(admin, [admin], next_scalar_result=admin)
    login(client, "admin")

    response = client.post(
        "/api/admin/users",
        json={
            "username": "ADMIN",
            "password": "another-secure-password",
            "role": "viewer",
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Username already exists"}
    assert session.added_user is None


def test_create_user_rejects_short_password(client: TestClient) -> None:
    admin = make_user(1, "admin", "admin")
    session = use_fake_session(admin, [admin])
    login(client, "admin")

    response = client.post(
        "/api/admin/users",
        json={"username": "viewer", "password": "short", "role": "viewer"},
    )

    assert response.status_code == 422
    assert session.added_user is None


def test_admin_can_deactivate_viewer(client: TestClient) -> None:
    admin = make_user(1, "admin", "admin")
    viewer = make_user(2, "viewer", "viewer")
    session = use_fake_session(admin, [admin, viewer])
    login(client, "admin")

    response = client.patch(
        "/api/admin/users/2/status",
        json={"is_active": False},
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert viewer.is_active is False
    assert session.committed is True


def test_update_status_returns_404_for_unknown_user(client: TestClient) -> None:
    admin = make_user(1, "admin", "admin")
    session = use_fake_session(admin, [admin])
    login(client, "admin")

    response = client.patch(
        "/api/admin/users/999/status",
        json={"is_active": False},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}
    assert session.committed is False


def test_last_active_admin_cannot_be_deactivated(client: TestClient) -> None:
    admin = make_user(1, "admin", "admin")
    session = use_fake_session(admin, [admin], next_scalar_result=1)
    login(client, "admin")

    response = client.patch(
        "/api/admin/users/1/status",
        json={"is_active": False},
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Last active admin cannot be deactivated"
    }
    assert admin.is_active is True
    assert session.committed is False


def test_admin_can_be_deactivated_when_another_admin_is_active(
    client: TestClient,
) -> None:
    first_admin = make_user(1, "admin", "admin")
    second_admin = make_user(2, "secondadmin", "admin")
    session = use_fake_session(
        first_admin,
        [first_admin, second_admin],
        next_scalar_result=2,
    )
    login(client, "admin")

    response = client.patch(
        "/api/admin/users/2/status",
        json={"is_active": False},
    )

    assert response.status_code == 200
    assert second_admin.is_active is False
    assert session.committed is True


def test_inactive_user_session_is_rejected_on_next_request(
    client: TestClient,
) -> None:
    viewer = make_user(2, "viewer", "viewer")
    use_fake_session(viewer, [viewer])
    login(client, "viewer")
    viewer.is_active = False

    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
