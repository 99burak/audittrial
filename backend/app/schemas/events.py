from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, IPvAnyAddress, field_validator


class AuditEventCreate(BaseModel):
    actor_id: str = Field(min_length=1, max_length=255)
    action: str = Field(min_length=1, max_length=100)
    resource_type: str = Field(min_length=1, max_length=100)
    resource_id: str = Field(min_length=1, max_length=255)
    old_values: dict[str, Any] | None = None
    new_values: dict[str, Any] | None = None
    ip_address: IPvAnyAddress | None = None
    metadata: dict[str, Any] | None = None
    occurred_at: datetime

    @field_validator("actor_id", "action", "resource_type", "resource_id")
    @classmethod
    def required_text_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value cannot be blank")
        return value

    @field_validator("occurred_at")
    @classmethod
    def occurred_at_must_include_timezone(cls, value: datetime) -> datetime:
        if value.utcoffset() is None:
            raise ValueError("occurred_at must include a timezone")
        return value


class AuditEventResponse(BaseModel):
    id: int
    application_id: int
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    old_values: dict[str, Any] | None
    new_values: dict[str, Any] | None
    ip_address: IPvAnyAddress | None
    metadata: dict[str, Any] | None
    occurred_at: datetime
    received_at: datetime


class AuditEventListResponse(BaseModel):
    items: list[AuditEventResponse]
    page: int
    page_size: int
    total: int
