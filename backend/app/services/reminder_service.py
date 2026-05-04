from __future__ import annotations

import asyncio
import smtplib
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from email.message import EmailMessage

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.constants import FINE_PER_OVERDUE_DAY
from app.models import Loan, LoanReminderLog
from app.services.fine_preview import projected_fine_if_returned_now

log = structlog.get_logger(__name__)

REMINDER_DUE_WITHIN_48H = "due_within_48h"
REMINDER_DUE_CALENDAR_DAY = "due_calendar_day"
REMINDER_OVERDUE_FINE_DAILY = "overdue_fine_daily"


def _brl(d: Decimal) -> str:
    s = f"{d.quantize(Decimal('0.01')):.2f}"
    return s.replace(".", ",")


def _loan_due_date_utc(loan: Loan) -> date:
    due = loan.due_at
    if due.tzinfo is None:
        due = due.replace(tzinfo=timezone.utc)
    else:
        due = due.astimezone(timezone.utc)
    return due.date()


def _send_plain_email_sync(to_email: str, subject: str, body_plain: str) -> bool:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg.set_content(body_plain, charset="utf-8")
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(msg)
        return True
    except (OSError, smtplib.SMTPException) as e:
        log.exception("smtp_plain_error", error=str(e))
        return False


async def _send_plain_email(to_email: str, subject: str, body_plain: str) -> bool:
    return await asyncio.to_thread(_send_plain_email_sync, to_email, subject, body_plain)


async def run_due_within_48h_reminders(
    session: AsyncSession, now: datetime | None = None
) -> None:
    """
    Active loans with due_at in (now, now + 48h] (UTC-aware), **exceto** os que vencem
    **no dia UTC atual** (esses só na tarefa `due_calendar_day`, para não duplicar nem dizer
    “48 horas” quando o vencimento é hoje).

    Idempotency via loan_reminder_logs; email + webhook as configured.

    Commit **por empréstimo**: se um candidato falhar no fim, não desfaz notificação in-app
    e logs já gravados para os anteriores (e-mail pode já ter sido enviado).
    """
    now = now if now is not None else datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    window_end = now + timedelta(hours=48)
    utc_today = now.date()

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
    raw = list(result.unique().scalars().all())
    candidates: list[Loan] = []
    for loan in raw:
        due = loan.due_at
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        if due.date() == utc_today:
            continue
        candidates.append(loan)
    log.info(
        "reminder_scan_window",
        now=now.isoformat(),
        window_end=window_end.isoformat(),
        raw_count=len(raw),
        candidate_count=len(candidates),
        loan_ids=[loan.id for loan in candidates],
        smtp_configured=settings.smtp_configured,
    )
    for loan in candidates:
        due = loan.due_at
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        due_date = due.date()
        try:
            await _dispatch_reminder(session, loan, due_date, REMINDER_DUE_WITHIN_48H, now)
            await session.commit()
        except Exception:
            await session.rollback()
            log.exception("loan_reminder_dispatch_failed", loan_id=getattr(loan, "id", None))


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

    if row.in_app_sent_at is None:
        from app.services import notification_service

        due_disp = _due_at_for_display(loan)
        due_txt = due_disp.strftime("%d/%m/%Y %H:%M UTC")
        book_title = loan.book.title if loan.book is not None else "o exemplar"
        await notification_service.create_notification(
            session,
            loan.user_id,
            "Prazo de devolução próximo",
            f"«{book_title}» vence nas próximas 48 horas (previsto: {due_txt}). Devolva no prazo para evitar multa.",
            kind="loan_due_within_48h",
        )
        row.in_app_sent_at = now
        await session.flush()
        log.info(
            "loan_reminder_in_app_created",
            loan_id=loan.id,
            user_id=loan.user_id,
            reminder_kind=reminder_kind,
        )

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

    subject = f'Marginália — "{title}" is due within 48 hours'

    body_plain = (
        f"Olá {patron},\n\n"
        "A data de devolução do seu empréstimo vence em 48 horas. Detalhes:\n\n"
        f"  Livro      {title}\n"
        f"  Data de devolução  {due_line}\n\n"
        "Por favor, se atente a data de retorno do livro para evitar cobranças de atraso.\n\n"
        "— Marginália\n"
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


async def run_due_calendar_day_notices(
    session: AsyncSession, now: datetime | None = None
) -> None:
    """Notificação in-app e e-mail (se SMTP) no dia (UTC) do vencimento; sem webhook."""

    now = now if now is not None else datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    today_start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
    tomorrow_start = today_start + timedelta(days=1)

    q = (
        select(Loan)
        .options(selectinload(Loan.user), selectinload(Loan.book))
        .where(
            Loan.returned_at.is_(None),
            Loan.due_at >= today_start,
            Loan.due_at < tomorrow_start,
        )
    )
    result = await session.execute(q)
    candidates = list(result.unique().scalars().all())
    log.info(
        "due_calendar_day_scan",
        count=len(candidates),
        loan_ids=[x.id for x in candidates],
    )
    for loan in candidates:
        due = loan.due_at
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        log_due_date = due.date()
        try:
            await _dispatch_due_calendar_notice(
                session, loan, log_due_date, REMINDER_DUE_CALENDAR_DAY, now
            )
            await session.commit()
        except Exception:
            await session.rollback()
            log.exception("due_calendar_notice_failed", loan_id=loan.id)


async def _dispatch_due_calendar_notice(
    session: AsyncSession,
    loan: Loan,
    log_due_date: date,
    reminder_kind: str,
    now: datetime,
) -> None:
    from app.services import notification_service

    row = await session.scalar(
        select(LoanReminderLog).where(
            LoanReminderLog.loan_id == loan.id,
            LoanReminderLog.due_date == log_due_date,
            LoanReminderLog.reminder_kind == reminder_kind,
        )
    )
    if row is None:
        row = LoanReminderLog(
            loan_id=loan.id,
            due_date=log_due_date,
            reminder_kind=reminder_kind,
        )
        session.add(row)
        await session.flush()

    book_title = loan.book.title if loan.book is not None else "o exemplar"
    rate = _brl(FINE_PER_OVERDUE_DAY)

    if row.in_app_sent_at is None:
        await notification_service.create_notification(
            session,
            loan.user_id,
            "Vencimento hoje",
            f"Hoje é o prazo de devolução de «{book_title}». Após hoje, incidem R$ {rate} "
            "por dia civil de atraso até a devolução.",
            kind=reminder_kind,
        )
        row.in_app_sent_at = now
        await session.flush()
        log.info("due_calendar_in_app_sent", loan_id=loan.id, user_id=loan.user_id)

    if row.email_sent_at is None and settings.smtp_configured and loan.user is not None:
        patron = loan.user.name or "Olá"
        to_email = loan.user.email
        if to_email and await _send_plain_email(
            to_email,
            f'Marginália — Vencimento hoje: «{book_title}»',
            (
                f"Olá, {patron},\n\n"
                f"Hoje é o prazo de devolução de «{book_title}». Após hoje, incidem R$ {rate} "
                "por dia civil de atraso até a devolução.\n\n"
                "— Marginália\n"
            ),
        ):
            row.email_sent_at = now
            await session.flush()
            log.info(
                "due_calendar_email_sent",
                loan_id=loan.id,
                user_id=loan.user_id,
            )


async def run_daily_overdue_fine_notices(
    session: AsyncSession, now: datetime | None = None
) -> None:
    """Uma notificação in-app e e-mail (se SMTP) por dia (UTC) com a multa acumulada; sem webhook."""

    now = now if now is not None else datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    today_date = now.date()

    q = (
        select(Loan)
        .options(selectinload(Loan.user), selectinload(Loan.book))
        .where(Loan.returned_at.is_(None), Loan.due_at < now)
    )
    result = await session.execute(q)
    candidates = list(result.unique().scalars().all())
    fine_positive: list[tuple[Loan, Decimal]] = []
    for loan in candidates:
        fine = projected_fine_if_returned_now(loan.due_at, returned_at=None, as_of=now)
        if fine is not None and fine > 0:
            fine_positive.append((loan, fine))
    log.info(
        "overdue_fine_daily_scan",
        candidate_loans=len(candidates),
        fine_positive_count=len(fine_positive),
        loan_ids=[t[0].id for t in fine_positive],
    )
    for loan, fine in fine_positive:
        try:
            await _dispatch_overdue_fine_daily(session, loan, today_date, fine, now)
            await session.commit()
        except Exception:
            await session.rollback()
            log.exception("overdue_fine_daily_failed", loan_id=loan.id)


async def _dispatch_overdue_fine_daily(
    session: AsyncSession,
    loan: Loan,
    notification_calendar_date: date,
    fine: Decimal,
    now: datetime,
) -> None:
    from app.services import notification_service

    reminder_kind = REMINDER_OVERDUE_FINE_DAILY
    row = await session.scalar(
        select(LoanReminderLog).where(
            LoanReminderLog.loan_id == loan.id,
            LoanReminderLog.due_date == notification_calendar_date,
            LoanReminderLog.reminder_kind == reminder_kind,
        )
    )
    if row is None:
        row = LoanReminderLog(
            loan_id=loan.id,
            due_date=notification_calendar_date,
            reminder_kind=reminder_kind,
        )
        session.add(row)
        await session.flush()

    current_due_date_utc = _loan_due_date_utc(loan)
    stored_due_snapshot = row.loan_due_at_utc_snapshot
    if stored_due_snapshot is not None and stored_due_snapshot != current_due_date_utc:
        row.in_app_sent_at = None
        row.email_sent_at = None
        await session.flush()
        log.info(
            "overdue_fine_daily_reset_after_loan_due_change",
            loan_id=loan.id,
            stored_snapshot=str(stored_due_snapshot),
            current_due_date_utc=str(current_due_date_utc),
        )

    book_title = loan.book.title if loan.book is not None else "o exemplar"
    amt = _brl(fine)
    per_day = _brl(FINE_PER_OVERDUE_DAY)

    if row.in_app_sent_at is None:
        await notification_service.create_notification(
            session,
            loan.user_id,
            "Multa por atraso (atualizada)",
            f"«{book_title}» está em atraso. Multa acumulada até hoje: R$ {amt} "
            f"(R$ {per_day} por dia civil). Devolva o exemplar para encerrar a cobrança.",
            kind=reminder_kind,
        )
        row.in_app_sent_at = now
        row.loan_due_at_utc_snapshot = current_due_date_utc
        await session.flush()
        log.info(
            "overdue_fine_daily_in_app_sent",
            loan_id=loan.id,
            user_id=loan.user_id,
            fine=str(fine),
        )

    if row.email_sent_at is None and settings.smtp_configured and loan.user is not None:
        patron = loan.user.name or "Olá"
        to_email = loan.user.email
        if to_email and await _send_plain_email(
            to_email,
            f'Marginália — Multa por atraso: «{book_title}»',
            (
                f"Olá, {patron},\n\n"
                f"«{book_title}» está em atraso. Multa acumulada até hoje: R$ {amt} "
                f"(R$ {per_day} por dia civil). Devolva o exemplar para encerrar a cobrança.\n\n"
                "— Marginália\n"
            ),
        ):
            row.email_sent_at = now
            await session.flush()
            log.info(
                "overdue_fine_daily_email_sent",
                loan_id=loan.id,
                user_id=loan.user_id,
                fine=str(fine),
            )
