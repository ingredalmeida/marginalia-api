from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuthorCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"name": "Clarice Lispector", "bio": "Brazilian writer."}}
    )

    name: str = Field(min_length=1, max_length=255)
    bio: str | None = Field(default=None, max_length=5000)


class AuthorUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"name": "Clarice Lispector", "bio": "Updated bio."}}
    )

    name: str | None = Field(default=None, min_length=1, max_length=255)
    bio: str | None = Field(default=None, max_length=5000)


class AuthorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    bio: str | None
    created_at: datetime
