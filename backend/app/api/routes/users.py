from fastapi import APIRouter, HTTPException, Path, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import AdminUser, DatabaseSession
from app.core.security import hash_password
from app.models import User
from app.schemas.auth import UserResponse
from app.schemas.users import UserCreate, UserStatusUpdate

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


@router.patch("/{user_id}/status", response_model=UserResponse)
def update_user_status(
    status_data: UserStatusUpdate,
    session: DatabaseSession,
    admin_user: AdminUser,
    user_id: int = Path(gt=0),
) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.is_active == status_data.is_active:
        return user

    if user.role == "admin" and status_data.is_active is False:
        active_admin_count = session.scalar(
            select(func.count())
            .select_from(User)
            .where(User.role == "admin", User.is_active.is_(True))
        )
        if active_admin_count is None or active_admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Last active admin cannot be deactivated",
            )

    user.is_active = status_data.is_active
    session.commit()
    session.refresh(user)
    return user

