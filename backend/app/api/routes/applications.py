from fastapi import APIRouter, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import AdminUser, DatabaseSession
from app.models import Application
from app.schemas.applications import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationStatusUpdate,
)

router = APIRouter(prefix="/admin/applications", tags=["admin-applications"])


@router.get("", response_model=list[ApplicationResponse])
def list_applications(
    session: DatabaseSession,
    admin_user: AdminUser,
) -> list[Application]:
    statement = select(Application).order_by(Application.id)
    return list(session.scalars(statement).all())


@router.post(
    "",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_application(
    application_data: ApplicationCreate,
    session: DatabaseSession,
    admin_user: AdminUser,
) -> Application:
    name = application_data.name.strip()
    existing_application = session.scalar(
        select(Application).where(Application.name == name)
    )
    if existing_application is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Application name already exists",
        )

    description = application_data.description
    if description is not None:
        description = description.strip() or None

    application = Application(name=name, description=description, is_active=True)
    session.add(application)

    try:
        session.commit()
        session.refresh(application)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Application name already exists",
        ) from None

    return application


@router.patch("/{application_id}/status", response_model=ApplicationResponse)
def update_application_status(
    status_data: ApplicationStatusUpdate,
    session: DatabaseSession,
    admin_user: AdminUser,
    application_id: int = Path(gt=0),
) -> Application:
    application = session.get(Application, application_id)
    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    if application.is_active == status_data.is_active:
        return application

    application.is_active = status_data.is_active
    session.commit()
    session.refresh(application)
    return application
