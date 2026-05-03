"""Celery tasks for loan due reminders."""

import asyncio

import structlog

from app.celery_app import celery
from app.core.database import AsyncSessionLocal
from app.core.logging_config import configure_logging
from app.services.reminder_service import run_due_within_48h_reminders

log = structlog.get_logger(__name__)


async def _run_reminders_async() -> None:
    async with AsyncSessionLocal() as session:
        await run_due_within_48h_reminders(session)


@celery.task(name="app.tasks.reminders.scan_loans_due_within_48_hours")
def scan_loans_due_within_48_hours() -> None:
    """Scheduled hourly: notify active loans whose due_at falls within the next 48 hours."""
    configure_logging()
    try:
        asyncio.run(_run_reminders_async())
    except Exception:
        log.exception("celery_reminder_task_failed")
        raise
