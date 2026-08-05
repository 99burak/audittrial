import argparse
import getpass
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import User

MIN_PASSWORD_LENGTH = 12


def create_admin(session: Session, username: str, password: str) -> User:
    normalized_username = username.strip().lower()

    if not normalized_username:
        raise ValueError("Username cannot be empty.")
    if len(normalized_username) > 100:
        raise ValueError("Username cannot be longer than 100 characters.")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must contain at least {MIN_PASSWORD_LENGTH} characters."
        )

    existing_user = session.scalar(
        select(User).where(User.username == normalized_username)
    )
    if existing_user is not None:
        raise ValueError("A user with this username already exists.")

    admin = User(
        username=normalized_username,
        password_hash=hash_password(password),
        role="admin",
        is_active=True,
    )
    session.add(admin)

    try:
        session.commit()
        session.refresh(admin)
    except SQLAlchemyError:
        session.rollback()
        raise

    return admin


def run_create_admin(
    input_func: Callable[[str], str] = input,
    password_func: Callable[[str], str] = getpass.getpass,
    session_factory: Callable[[], Session] = SessionLocal,
) -> int:
    username = input_func("Admin username: ")
    password = password_func("Admin password: ")
    password_confirmation = password_func("Confirm password: ")

    if password != password_confirmation:
        print("Error: passwords do not match.")
        return 1

    try:
        with session_factory() as session:
            admin = create_admin(session, username, password)
    except ValueError as error:
        print(f"Error: {error}")
        return 1
    except SQLAlchemyError:
        print("Error: admin user could not be created.")
        return 1

    print(f"Admin user created: {admin.username}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="AuditTrail administration commands")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("create-admin", help="Create the first panel admin")
    arguments = parser.parse_args()

    if arguments.command == "create-admin":
        return run_create_admin()

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

