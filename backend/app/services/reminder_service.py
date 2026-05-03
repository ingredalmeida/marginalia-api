from __future__ import annotations

import asyncio
import smtplib
from datetime import date, datetime, timedelta, timezone
from email.message import EmailMessage

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models import Loan, LoanReminderLog

log = structlog.get_logger(__name__)

REMINDER_DUE_WITHIN_48H = "due_within_48h"


async def run_due_within_48h_reminders(
    session: AsyncSession, now: datetime | None = None
) -> None:
    """
    Active loans with due_at in (now, now + 48h] (UTC-aware).
    Idempotency via loan_reminder_logs; email + webhook as configured.
    """
    now = now if now is not None else datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    window_end = now + timedelta(hours=48)

    q = (
        select(Loan)
        .options(selectinload(Loan.user), selectinload(Loan.book))
        .where(
            Loan.returned_at.is_(None),
            Loan.due_at > now,
            Loan.due_at <= window_end,
        )
    )
    result = await session.execute(q)
    candidates = list(result.unique().scalars().all())
    log.info(
        "reminder_scan_window",
        now=now.isoformat(),
        window_end=window_end.isoformat(),
        candidate_count=len(candidates),
        loan_ids=[loan.id for loan in candidates],
        smtp_configured=settings.smtp_configured,
    )
    for loan in candidates:
        due = loan.due_at
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        due_date = due.date()
        await _dispatch_reminder(session, loan, due_date, REMINDER_DUE_WITHIN_48H, now)

    await session.commit()


async def _dispatch_reminder(
    session: AsyncSession,
    loan: Loan,
    due_date: date,
    reminder_kind: str,
    now: datetime,
) -> None:
    row = await session.scalar(
        select(LoanReminderLog).where(
            LoanReminderLog.loan_id == loan.id,
            LoanReminderLog.due_date == due_date,
            LoanReminderLog.reminder_kind == reminder_kind,
        )
    )
    if row is None:
        row = LoanReminderLog(
            loan_id=loan.id,
            due_date=due_date,
            reminder_kind=reminder_kind,
        )
        session.add(row)
        await session.flush()

    payload = _build_payload(loan, reminder_kind)

    if row.email_sent_at is None:
        if settings.smtp_configured:
            if await _send_email(loan):
                row.email_sent_at = now
                log.info(
                    "loan_reminder_email_sent",
                    loan_id=loan.id,
                    reminder_kind=reminder_kind,
                    user_email=loan.user.email,
                )
            else:
                log.warning(
                    "loan_reminder_email_failed",
                    loan_id=loan.id,
                    reminder_kind=reminder_kind,
                )
        else:
            log.warning(
                "loan_reminder_smtp_skipped",
                loan_id=loan.id,
                reminder_kind=reminder_kind,
                hint="Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD for celery_worker (e.g. backend/.env).",
            )
    if row.webhook_sent_at is None and settings.loan_reminder_webhook_url:
        if await _post_webhook(payload):
            row.webhook_sent_at = now
            log.info(
                "loan_reminder_webhook_sent",
                loan_id=loan.id,
                reminder_kind=reminder_kind,
            )
        else:
            log.warning(
                "loan_reminder_webhook_failed",
                loan_id=loan.id,
                reminder_kind=reminder_kind,
            )


def _due_at_for_display(loan: Loan) -> datetime:
    due = loan.due_at
    if due.tzinfo is None:
        due = due.replace(tzinfo=timezone.utc)
    return due.astimezone(timezone.utc)


def _format_due_human(due: datetime) -> str:
    """English, UTC, e.g. Saturday, May 3, 2026 · 16:42 UTC."""
    return (
        due.strftime("%A, %B ")
        + str(due.day)
        + due.strftime(", %Y · %H:%M UTC")
    )


def _build_payload(loan: Loan, reminder_kind: str) -> dict:
    due = loan.due_at
    if due.tzinfo is None:
        due = due.replace(tzinfo=timezone.utc)
    return {
        "event": "loan_due_reminder",
        "reminder_kind": reminder_kind,
        "loan_id": loan.id,
        "user_id": loan.user_id,
        "user_email": loan.user.email,
        "user_name": loan.user.name,
        "book_id": loan.book_id,
        "book_title": loan.book.title,
        "due_at": due.isoformat(),
    }


def _send_email_sync(loan: Loan) -> bool:
    """Blocking SMTP (run via asyncio.to_thread from async callers)."""
    due = _due_at_for_display(loan)
    due_line = _format_due_human(due)
    title = loan.book.title
    patron = loan.user.name

    subject = f'LaBiblioteca — "{title}" is due within 48 hours'

    body_plain = (
        f"Hello {patron},\n\n"
        "Your loan is due within the next 48 hours. Details:\n\n"
        f"  Book      {title}\n"
        f"  Due date  {due_line}\n\n"
        "Please return the copy on or before that time to avoid late fees.\n\n"
        "— LaBiblioteca\n"
    )

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = loan.user.email
    msg.set_content(body_plain, charset="utf-8")

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(msg)
        return True
    except (OSError, smtplib.SMTPException) as e:
        log.exception("smtp_error", error=str(e))
        return False


async def _send_email(loan: Loan) -> bool:
    return await asyncio.to_thread(_send_email_sync, loan)


async def _post_webhook(payload: dict) -> bool:
    url = settings.loan_reminder_webhook_url
    if not url:
        return False
    try:
        timeout = httpx.Timeout(settings.webhook_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
        if r.is_success:
            return True
        log.warning(
            "webhook_non_success",
            status_code=r.status_code,
            body_preview=r.text[:500],
        )
        return False
    except httpx.HTTPError as e:
        log.exception("webhook_http_error", error=str(e))
        return False
