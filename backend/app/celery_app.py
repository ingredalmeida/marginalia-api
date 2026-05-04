"""Celery application: broker Redis (separate DB index from cache); Beat schedules hourly tasks."""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery = Celery(
    "marginalia",
    broker=settings.celery_broker_url,
    include=["app.tasks.reminders", "app.tasks.holds"],
)

celery.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_ignore_result=True,
    broker_connection_retry_on_startup=True,
)

celery.conf.beat_schedule = {
    "scan-loans-due-within-48-hours": {
        "task": "app.tasks.reminders.scan_loans_due_within_48_hours",
        "schedule": crontab(minute=0),
    },
    "scan-loans-due-calendar-day": {
        "task": "app.tasks.reminders.scan_loans_due_calendar_day",
        "schedule": crontab(minute=0),
    },
    "scan-loans-overdue-fine-daily": {
        "task": "app.tasks.reminders.scan_loans_overdue_fine_daily",
        "schedule": crontab(minute=0),
    },
    "expire-reservation-holds": {
        "task": "app.tasks.holds.expire_reservation_holds",
        "schedule": crontab(minute="*"),
    },
}
