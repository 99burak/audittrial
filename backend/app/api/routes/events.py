from datetime import UTC, datetime

from fastapi import APIRouter, Query, status
from sqlalchemy import func, select

from app.api.dependencies import (
    AuthenticatedApiKey,
    CurrentUser,
    DatabaseSession,
)
from app.models import AuditEvent
from app.schemas.events import (
    AuditEventCreate,
    AuditEventListResponse,
    AuditEventResponse,
)

router = APIRouter(prefix="/events", tags=["events"])


def to_event_response(event: AuditEvent) -> AuditEventResponse:
    return AuditEventResponse(
        id=event.id,
        application_id=event.application_id,
        actor_id=event.actor_id,
        action=event.action,
        resource_type=event.resource_type,
        resource_id=event.resource_id,
        old_values=event.old_values,
        new_values=event.new_values,
        ip_address=event.ip_address,
        metadata=event.event_metadata,
        occurred_at=event.occurred_at,
        received_at=event.received_at,
    )


@router.get("", response_model=AuditEventListResponse)
def list_events(
    session: DatabaseSession,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> AuditEventListResponse:
    total = session.scalar(select(func.count()).select_from(AuditEvent)) or 0
    statement = (
        select(AuditEvent)
        .order_by(AuditEvent.received_at.desc(), AuditEvent.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    events = list(session.scalars(statement).all())

    return AuditEventListResponse(
        items=[to_event_response(event) for event in events],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post(
    "",
    response_model=AuditEventResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_event(
    event_data: AuditEventCreate,
    session: DatabaseSession,
    api_key: AuthenticatedApiKey,
) -> AuditEventResponse:
    event = AuditEvent(
        application_id=api_key.application_id,
        actor_id=event_data.actor_id,
        action=event_data.action,
        resource_type=event_data.resource_type,
        resource_id=event_data.resource_id,
        old_values=event_data.old_values,
        new_values=event_data.new_values,
        ip_address=(
            str(event_data.ip_address)
            if event_data.ip_address is not None
            else None
        ),
        event_metadata=event_data.metadata,
        occurred_at=event_data.occurred_at,
    )
    api_key.last_used_at = datetime.now(UTC)
    session.add(event)
    session.commit()
    session.refresh(event)

    return to_event_response(event)
