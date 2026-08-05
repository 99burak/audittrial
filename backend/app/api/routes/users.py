from fastapi import APIRouter
from sqlalchemy import select

from app.api.dependencies import AdminUser, DatabaseSession
from app.models import User
from app.schemas.auth import UserResponse

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


@router.get("", response_model=list[UserResponse])
def list_users(session: DatabaseSession, admin_user: AdminUser) -> list[User]:
    statement = select(User).order_by(User.id)
    return list(session.scalars(statement).all())

