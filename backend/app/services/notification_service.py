from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Notification


async def create_notification(
    session: AsyncSession,
    user_id: int,
    title: str,
    body: str,
    kind: str = "info",
    ref_reservation_id: int | None = None,
) -> Notification:
    n = Notification(
        user_id=user_id,
        title=title,
        body=body,
        kind=kind,
        ref_reservation_id=ref_reservation_id,
    )
    session.add(n)
    await session.flush()
    return n


async def unread_count(session: AsyncSession, user_id: int) -> int:
    q = select(func.count()).select_from(Notification).where(
        Notification.user_id == user_id,
        Notification.read_at.is_(None),
    )
    return int((await session.scalar(q)) or 0)


async def list_recent(
    session: AsyncSession, user_id: int, limit: int = 30
) -> list[Notification]:
    result = await session.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def mark_read(session: AsyncSession, notification_id: int, user_id: int) -> None:
    result = await session.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    )
    n = result.scalar_one_or_none()
    if n is None:
        return
    if n.read_at is None:
        n.read_at = datetime.now(timezone.utc)
        await session.flush()


async def mark_all_read(session: AsyncSession, user_id: int) -> None:
    now = datetime.now(timezone.utc)
    rows = await session.execute(
        select(Notification).where(
            Notification.user_id == user_id,
            Notification.read_at.is_(None),
        )
    )
    for n in rows.scalars():
        n.read_at = now
    await session.flush()
