from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_db
from app.core.security import hash_password
from app.main import app
from app.models import User


class FakeSession:
    def __init__(self, user: User | None) -> None:
        self.user = user

    def scalar(self, statement) -> User | None:
        return self.user

    def get(self, model, object_id: int) -> User | None:
        if self.user is not None and self.user.id == object_id:
            return self.user
        return None


def make_user(*, is_active: bool = True) -> User:
    user = User(
        username="admin",
        password_hash=hash_password("a-secure-admin-password"),
        role="admin",
        is_active=is_active,
    )
    user.id = 1
    return user


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def use_fake_session(user: User | None) -> None:
    fake_session = FakeSession(user)

    def override_get_db():
        yield fake_session

    app.dependency_overrides[get_db] = override_get_db


def test_login_sets_session_cookie_and_hides_password_hash(client: TestClient) -> None:
    use_fake_session(make_user())

    response = client.post(
        "/api/auth/login",
        json={"username": " ADMIN ", "password": "a-secure-admin-password"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "username": "admin",
        "role": "admin",
        "is_active": True,
    }
    assert "audittrail_session" in response.cookies
    assert "password_hash" not in response.text


def test_login_rejects_wrong_password(client: TestClient) -> None:
    use_fake_session(make_user())

    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid username or password"}


def test_login_rejects_inactive_user(client: TestClient) -> None:
    use_fake_session(make_user(is_active=False))

    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "a-secure-admin-password"},
    )

    assert response.status_code == 401


def test_me_requires_authentication(client: TestClient) -> None:
    use_fake_session(make_user())

    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_me_returns_current_user_after_login(client: TestClient) -> None:
    use_fake_session(make_user())
    login_response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "a-secure-admin-password"},
    )

    response = client.get("/api/auth/me")

    assert login_response.status_code == 200
    assert response.status_code == 200
    assert response.json()["username"] == "admin"


def test_logout_clears_session(client: TestClient) -> None:
    use_fake_session(make_user())
    client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "a-secure-admin-password"},
    )

    logout_response = client.post("/api/auth/logout")
    me_response = client.get("/api/auth/me")

    assert logout_response.status_code == 204
    assert me_response.status_code == 401

