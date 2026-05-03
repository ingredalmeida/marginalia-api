from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReservationCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"user_id": 1, "book_id": 1}})

    user_id: int = Field(ge=1)
    book_id: int = Field(ge=1)


class ReservationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    book_id: int
    status: str
    created_at: datetime
    hold_until: datetime | None = None
    book_title: str | None = None
    author_name: str | None = None
    queue_position: int | None = None
