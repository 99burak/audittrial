from fastapi import APIRouter, HTTPException, Request, Response, status
from sqlalchemy import select

from app.api.dependencies import CurrentUser, DatabaseSession
from app.core.security import verify_password
from app.models import User
from app.schemas.auth import LoginRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=UserResponse)
def login(
    credentials: LoginRequest,
    request: Request,
    session: DatabaseSession,
) -> User:
    username = credentials.username.strip().lower()
    user = session.scalar(select(User).where(User.username == username))

    if user is None or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    request.session.clear()
    request.session["user_id"] = user.id
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request) -> Response:
    request.session.clear()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserResponse)
def me(current_user: CurrentUser) -> User:
    return current_user

