from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User
from app.schemas.notification import NotificationRead, NotificationUnreadCount
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=list[NotificationRead])
async def list_notifications(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    limit: int = Query(30, ge=1, le=100),
) -> list[NotificationRead]:
    rows = await notification_service.list_recent(db, current.id, limit)
    return [NotificationRead.model_validate(x) for x in rows]


@router.get("/unread-count", response_model=NotificationUnreadCount)
async def unread_count_route(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> NotificationUnreadCount:
    n = await notification_service.unread_count(db, current.id)
    return NotificationUnreadCount(count=n)


@router.post("/{notification_id}/read", status_code=204)
async def mark_one_read(
    notification_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> None:
    await notification_service.mark_read(db, notification_id, current.id)
    await db.commit()


@router.post("/read-all", status_code=204)
async def mark_all_read_route(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> None:
    await notification_service.mark_all_read(db, current.id)
    await db.commit()


@router.post("/clear-all", status_code=204)
async def clear_all_notifications_route(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> None:
    await notification_service.delete_all_for_user(db, current.id)
    await db.commit()
