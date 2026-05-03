from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    body: str
    kind: str
    ref_reservation_id: int | None = None
    read_at: datetime | None
    created_at: datetime


class NotificationUnreadCount(BaseModel):
    count: int
