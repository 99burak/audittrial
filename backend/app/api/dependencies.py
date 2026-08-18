from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_api_key
from app.db.session import SessionLocal
from app.models import ApiKey, Application, User


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


def require_admin(current_user: CurrentUser) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    return current_user


AdminUser = Annotated[User, Depends(require_admin)]


def get_authenticated_api_key(
    session: DatabaseSession,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> ApiKey:
    api_key = None
    if x_api_key:
        api_key = session.scalar(
            select(ApiKey).where(ApiKey.key_hash == hash_api_key(x_api_key))
        )

    if api_key is None or api_key.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    application = session.get(Application, api_key.application_id)
    if application is None or not application.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return api_key


AuthenticatedApiKey = Annotated[ApiKey, Depends(get_authenticated_api_key)]
