"""Expire reservation hold windows and advance the waitlist."""

import asyncio

import structlog
from redis import Redis

from app.celery_app import celery
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.logging_config import configure_logging
from app.services import reservation_service

log = structlog.get_logger(__name__)


def _redis_client() -> Redis | None:
    if not settings.redis_url or not str(settings.redis_url).strip():
        return None
    return Redis.from_url(str(settings.redis_url), decode_responses=True)


async def _expire_async() -> int:
    r = _redis_client()
    async with AsyncSessionLocal() as session:
        n = await reservation_service.expire_expired_reservation_holds(session, r)
        await session.commit()
    if n:
        log.info("reservation_holds_expired", count=n)
    return n


@celery.task(name="app.tasks.holds.expire_reservation_holds")
def expire_reservation_holds() -> None:
    configure_logging()
    try:
        asyncio.run(_expire_async())
    except Exception:
        log.exception("expire_reservation_holds_failed")
        raise
