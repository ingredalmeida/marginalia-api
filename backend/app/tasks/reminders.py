"""Celery tasks for loan reminders: one task per flow (48h window, due calendar day, daily overdue fine)."""

import asyncio
from collections.abc import Awaitable, Callable

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery
from app.core.database import AsyncSessionLocal
from app.core.logging_config import configure_logging
from app.services.reminder_service import (
    run_daily_overdue_fine_notices,
    run_due_calendar_day_notices,
    run_due_within_48h_reminders,
)

log = structlog.get_logger(__name__)


async def _with_session(
    fn: Callable[[AsyncSession], Awaitable[None]],
) -> None:
    async with AsyncSessionLocal() as session:
        await fn(session)


def _run_reminder_task(
    fn: Callable[[AsyncSession], Awaitable[None]], task_label: str
) -> None:
    configure_logging()
    try:
        asyncio.run(_with_session(fn))
    except Exception:
        log.exception("celery_reminder_task_failed", task=task_label)
        raise


@celery.task(name="app.tasks.reminders.scan_loans_due_within_48_hours")
def scan_loans_due_within_48_hours() -> None:
    """Active loans with due_at in (now, now+48h], excluding same UTC calendar day as now."""
    _run_reminder_task(run_due_within_48h_reminders, "scan_loans_due_within_48_hours")


@celery.task(name="app.tasks.reminders.scan_loans_due_calendar_day")
def scan_loans_due_calendar_day() -> None:
    """Notices on the loan’s due UTC calendar day (in-app + email if SMTP). No webhook."""
    _run_reminder_task(run_due_calendar_day_notices, "scan_loans_due_calendar_day")


@celery.task(name="app.tasks.reminders.scan_loans_overdue_fine_daily")
def scan_loans_overdue_fine_daily() -> None:
    """Once per UTC day: overdue active loans with estimated fine greater than zero."""
    _run_reminder_task(run_daily_overdue_fine_notices, "scan_loans_overdue_fine_daily")
