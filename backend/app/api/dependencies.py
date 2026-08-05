from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import User


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session


DatabaseSession = Annotated[Session, Depends(get_db)]


def get_current_user(request: Request, session: DatabaseSession) -> User:
    user_id = request.session.get("user_id")
    if not isinstance(user_id, int):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user = session.get(User, user_id)
    if user is None or not user.is_active:
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]

