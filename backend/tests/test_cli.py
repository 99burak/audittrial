from contextlib import contextmanager

import pytest

from app.cli import create_admin, run_create_admin
from app.core.security import verify_password
from app.models import User


class FakeSession:
    def __init__(self, existing_user: User | None = None) -> None:
        self.existing_user = existing_user
        self.added_user: User | None = None
        self.committed = False
        self.rolled_back = False

    def scalar(self, statement) -> User | None:
        return self.existing_user

    def add(self, user: User) -> None:
        self.added_user = user

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def refresh(self, user: User) -> None:
        user.id = 1


def test_create_admin_normalizes_username_and_hashes_password() -> None:
    session = FakeSession()

    admin = create_admin(session, "  FirstAdmin  ", "a-secure-admin-password")

    assert admin.username == "firstadmin"
    assert admin.role == "admin"
    assert admin.is_active is True
    assert admin.password_hash != "a-secure-admin-password"
    assert verify_password("a-secure-admin-password", admin.password_hash) is True
    assert session.added_user is admin
    assert session.committed is True


def test_create_admin_rejects_short_password() -> None:
    session = FakeSession()

    with pytest.raises(ValueError, match="at least 12 characters"):
        create_admin(session, "admin", "too-short")

    assert session.added_user is None


def test_create_admin_rejects_duplicate_username() -> None:
    existing_user = User(
        username="admin",
        password_hash="existing-hash",
        role="admin",
        is_active=True,
    )
    session = FakeSession(existing_user=existing_user)

    with pytest.raises(ValueError, match="already exists"):
        create_admin(session, "ADMIN", "a-secure-admin-password")

    assert session.added_user is None


def test_cli_rejects_password_confirmation_mismatch(capsys) -> None:
    passwords = iter(["a-secure-admin-password", "different-password"])

    result = run_create_admin(
        input_func=lambda prompt: "admin",
        password_func=lambda prompt: next(passwords),
    )

    assert result == 1
    assert "passwords do not match" in capsys.readouterr().out


def test_cli_creates_admin_without_printing_password(capsys) -> None:
    session = FakeSession()
    passwords = iter(["a-secure-admin-password", "a-secure-admin-password"])

    @contextmanager
    def session_factory():
        yield session

    result = run_create_admin(
        input_func=lambda prompt: "Admin",
        password_func=lambda prompt: next(passwords),
        session_factory=session_factory,
    )

    output = capsys.readouterr().out
    assert result == 0
    assert "Admin user created: admin" in output
    assert "a-secure-admin-password" not in output

