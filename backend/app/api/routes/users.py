from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import AdminUser, DatabaseSession
from app.core.security import hash_password
from app.models import User
from app.schemas.auth import UserResponse
from app.schemas.users import UserCreate

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


@router.get("", response_model=list[UserResponse])
def list_users(session: DatabaseSession, admin_user: AdminUser) -> list[User]:
    statement = select(User).order_by(User.id)
    return list(session.scalars(statement).all())


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    session: DatabaseSession,
    admin_user: AdminUser,
) -> User:
    username = user_data.username.strip().lower()
    existing_user = session.scalar(select(User).where(User.username == username))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    user = User(
        username=username,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        is_active=True,
    )
    session.add(user)

    try:
        session.commit()
        session.refresh(user)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        ) from None

    return user

