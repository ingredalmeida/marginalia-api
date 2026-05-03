"""Agregados para o painel admin (JSON); exportações detalhadas continuam em report_service."""

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Book, Loan, Reservation, User
from app.schemas.dashboard import DashboardSummary, TopBookItem
from app.services.book_service import active_loan_book_ids
from app.services.report_service import period_bounds, top_books_in_period


async def dashboard_summary(
    session: AsyncSession, date_from: date, date_to: date
) -> DashboardSummary:
    start, end_excl = period_bounds(date_from, date_to)
    now = datetime.now(timezone.utc)

    book_titles_total = int(await session.scalar(select(func.count()).select_from(Book)) or 0)
    users_total = int(await session.scalar(select(func.count()).select_from(User)) or 0)

    active_loans = int(
        await session.scalar(
            select(func.count()).select_from(Loan).where(Loan.returned_at.is_(None))
        )
        or 0
    )

    overdue_loans = int(
        await session.scalar(
            select(func.count())
            .select_from(Loan)
            .where(Loan.returned_at.is_(None), Loan.due_at < now)
        )
        or 0
    )

    loans_started_in_period = int(
        await session.scalar(
            select(func.count())
            .select_from(Loan)
            .where(Loan.borrowed_at >= start, Loan.borrowed_at < end_excl)
        )
        or 0
    )

    fine_total = await session.scalar(
        select(func.coalesce(func.sum(Loan.fine_amount), 0)).where(
            Loan.returned_at.isnot(None),
            Loan.returned_at >= start,
            Loan.returned_at < end_excl,
            Loan.fine_amount.isnot(None),
            Loan.fine_amount > 0,
        )
    )
    if fine_total is None:
        total_dec = Decimal("0")
    elif isinstance(fine_total, Decimal):
        total_dec = fine_total
    else:
        total_dec = Decimal(str(fine_total))
    total_fines_brl = f"{total_dec.quantize(Decimal('0.01'))}"

    busy = await active_loan_book_ids(session)
    on_loan_titles = len(busy)
    available_titles = max(0, book_titles_total - on_loan_titles)

    top_raw = await top_books_in_period(session, date_from, date_to, 5)
    top_books = [
        TopBookItem(
            book_id=int(r["book_id"]),
            title=str(r["title"]),
            author_name=str(r["author_name"]),
            loan_count=int(r["loan_count"]),
        )
        for r in top_raw
    ]

    reservations_pending = int(
        await session.scalar(
            select(func.count()).select_from(Reservation).where(Reservation.status == "pending")
        )
        or 0
    )
    reservations_hold = int(
        await session.scalar(
            select(func.count()).select_from(Reservation).where(Reservation.status == "hold")
        )
        or 0
    )

    return DashboardSummary(
        date_from=date_from,
        date_to=date_to,
        book_titles_total=book_titles_total,
        users_total=users_total,
        active_loans=active_loans,
        overdue_loans=overdue_loans,
        loans_started_in_period=loans_started_in_period,
        total_fines_brl=total_fines_brl,
        available_titles=available_titles,
        on_loan_titles=on_loan_titles,
        reservations_pending=reservations_pending,
        reservations_hold=reservations_hold,
        top_books=top_books,
    )
