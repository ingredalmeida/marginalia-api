"""Read-only queries for admin CSV/PDF reports."""

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import Author, Book, Loan, User
from app.services.book_service import active_loan_book_ids


def period_bounds(date_from: date, date_to: date) -> tuple[datetime, datetime]:
    """Inclusive date_from/date_to in UTC → [start, end_exclusive)."""
    start = datetime.combine(date_from, time.min, tzinfo=timezone.utc)
    end_excl = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=timezone.utc)
    return start, end_excl


def _loan_status(loan: Loan, now: datetime) -> str:
    if loan.returned_at is not None:
        return "returned"
    due = loan.due_at
    if due.tzinfo is None:
        due = due.replace(tzinfo=timezone.utc)
    if now > due:
        return "overdue"
    return "active"


async def loans_in_period(
    session: AsyncSession, date_from: date, date_to: date
) -> list[dict[str, object]]:
    start, end_excl = period_bounds(date_from, date_to)
    now = datetime.now(timezone.utc)
    stmt = (
        select(Loan, User, Book, Author)
        .join(User, Loan.user_id == User.id)
        .join(Book, Loan.book_id == Book.id)
        .join(Author, Book.author_id == Author.id)
        .where(Loan.borrowed_at >= start, Loan.borrowed_at < end_excl)
        .order_by(Loan.borrowed_at.desc())
    )
    result = await session.execute(stmt)
    rows: list[dict[str, object]] = []
    for loan, user, book, author in result.all():
        rows.append(
            {
                "loan_id": loan.id,
                "user_email": user.email,
                "user_name": user.name,
                "book_title": book.title,
                "author_name": author.name,
                "borrowed_at": loan.borrowed_at.isoformat(),
                "due_at": loan.due_at.isoformat(),
                "returned_at": loan.returned_at.isoformat() if loan.returned_at else "",
                "fine_amount": str(loan.fine_amount) if loan.fine_amount is not None else "",
                "status": _loan_status(loan, now),
            }
        )
    return rows


async def fines_in_period(
    session: AsyncSession, date_from: date, date_to: date
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """
    Detail rows (one per loan with fine) + aggregate rows for charts
    (user_email, total_fine_brl).
    """
    start, end_excl = period_bounds(date_from, date_to)
    stmt = (
        select(Loan, User, Book)
        .join(User, Loan.user_id == User.id)
        .join(Book, Loan.book_id == Book.id)
        .where(
            Loan.returned_at.isnot(None),
            Loan.returned_at >= start,
            Loan.returned_at < end_excl,
            Loan.fine_amount.isnot(None),
            Loan.fine_amount > 0,
        )
        .order_by(Loan.returned_at.desc())
    )
    result = await session.execute(stmt)
    detail: list[dict[str, object]] = []
    for loan, user, book in result.all():
        detail.append(
            {
                "loan_id": loan.id,
                "user_email": user.email,
                "user_name": user.name,
                "book_title": book.title,
                "returned_at": loan.returned_at.isoformat() if loan.returned_at else "",
                "fine_amount_brl": str(loan.fine_amount),
            }
        )

    agg_stmt = (
        select(User.email, User.name, func.sum(Loan.fine_amount).label("total"))
        .join(Loan, Loan.user_id == User.id)
        .where(
            Loan.returned_at.isnot(None),
            Loan.returned_at >= start,
            Loan.returned_at < end_excl,
            Loan.fine_amount.isnot(None),
            Loan.fine_amount > 0,
        )
        .group_by(User.id, User.email, User.name)
        .order_by(func.sum(Loan.fine_amount).desc())
    )
    agg_result = await session.execute(agg_stmt)
    aggregates: list[dict[str, object]] = []
    for email, name, total in agg_result.all():
        t = total if isinstance(total, Decimal) else Decimal(str(total))
        aggregates.append(
            {
                "user_email": email,
                "user_name": name,
                "total_fine_brl": str(t),
            }
        )
    return detail, aggregates


async def top_books_in_period(
    session: AsyncSession, date_from: date, date_to: date, limit: int
) -> list[dict[str, object]]:
    start, end_excl = period_bounds(date_from, date_to)
    stmt = (
        select(Book.id, Book.title, Author.name, func.count(Loan.id).label("loan_count"))
        .select_from(Loan)
        .join(Book, Loan.book_id == Book.id)
        .join(Author, Book.author_id == Author.id)
        .where(Loan.borrowed_at >= start, Loan.borrowed_at < end_excl)
        .group_by(Book.id, Book.title, Author.name)
        .order_by(func.count(Loan.id).desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return [
        {"book_id": bid, "title": title, "author_name": aname, "loan_count": int(cnt)}
        for bid, title, aname, cnt in result.all()
    ]


async def inventory_snapshot(session: AsyncSession) -> list[dict[str, object]]:
    busy = await active_loan_book_ids(session)
    stmt = select(Book).options(joinedload(Book.author)).order_by(Book.id)
    result = await session.execute(stmt)
    books = result.scalars().unique().all()
    rows: list[dict[str, object]] = []
    for book in books:
        avail = book.id not in busy
        rows.append(
            {
                "book_id": book.id,
                "title": book.title,
                "author_name": book.author.name,
                "isbn": book.isbn or "",
                "publication_year": book.publication_year if book.publication_year is not None else "",
                "available": "yes" if avail else "no",
            }
        )
    return rows
