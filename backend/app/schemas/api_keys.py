from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("API key name cannot be blank")
        return value


class ApiKeyCreatedResponse(BaseModel):
    id: int
    application_id: int
    name: str
    key_prefix: str
    api_key: str
    created_at: datetime
