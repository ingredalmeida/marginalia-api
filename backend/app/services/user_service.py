from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, DomainError, NotFoundError
from app.core.security import hash_password
from app.models import Book, Loan, User
from app.schemas.common import Page
from app.schemas.loan import LoanListFilter, LoanRead, UserLoanFilter
from app.schemas.user import UserRead, UserUpdate
from app.services.pagination import paginate_selection, total_pages


async def _books_by_ids(session: AsyncSession, book_ids: set[int]) -> dict[int, Book]:
    """Carrega livros e autores em lote (evita depender de eager load na query paginada de empréstimos)."""
    if not book_ids:
        return {}
    result = await session.execute(
        select(Book).options(selectinload(Book.author)).where(Book.id.in_(book_ids))
    )
    return {b.id: b for b in result.scalars().unique().all()}


def _loan_read_with_book(loan: Loan, book: Book | None) -> LoanRead:
    book_title = book.title if book is not None else None
    author_name = None
    if book is not None and book.author is not None:
        author_name = book.author.name
    return LoanRead(
        id=loan.id,
        user_id=loan.user_id,
        book_id=loan.book_id,
        renewal_count=loan.renewal_count,
        borrowed_at=loan.borrowed_at,
        due_at=loan.due_at,
        returned_at=loan.returned_at,
        fine_amount=loan.fine_amount,
        created_at=loan.created_at,
        book_title=book_title,
        author_name=author_name,
    )


def _apply_user_loan_filter(q, flt: UserLoanFilter):
    now_dt = datetime.now(timezone.utc)
    if flt == UserLoanFilter.active:
        return q.where(Loan.returned_at.is_(None))
    if flt == UserLoanFilter.returned:
        return q.where(Loan.returned_at.is_not(None))
    if flt == UserLoanFilter.overdue:
        return q.where(Loan.returned_at.is_(None), Loan.due_at < now_dt)
    return q


async def get_user(session: AsyncSession, user_id: int) -> UserRead:
    user = await session.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found.")
    return UserRead.model_validate(user)


async def delete_user(session: AsyncSession, user_id: int) -> None:
    n = await session.scalar(
        select(func.count()).select_from(Loan).where(Loan.user_id == user_id)
    )
    if (n or 0) > 0:
        raise ConflictError("Cannot delete user with existing loans.")
    user = await session.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found.")
    await session.delete(user)
    await session.commit()


async def update_user(session: AsyncSession, user_id: int, data: UserUpdate) -> UserRead:
    user = await session.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found.")
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        raise DomainError("No fields to update.")
    if "password" in updates:
        plain = updates.pop("password")
        updates["hashed_password"] = hash_password(plain)
    if "email" in updates:
        updates["email"] = str(updates["email"]).lower()
    for key, value in updates.items():
        setattr(user, key, value)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise ConflictError("Email already registered.") from None
    await session.refresh(user)
    return UserRead.model_validate(user)


async def list_users(
    session: AsyncSession, page: int, page_size: int, search: str | None = None
) -> Page[UserRead]:
    base = select(User).order_by(User.id)
    count_q = select(func.count()).select_from(User)
    if search and search.strip():
        term = f"%{search.strip()}%"
        filt = or_(User.name.ilike(term), User.email.ilike(term))
        base = base.where(filt)
        count_q = count_q.where(filt)
    rows, total = await paginate_selection(session, base, count_q, page, page_size)
    return Page[UserRead](
        items=[UserRead.model_validate(u) for u in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=total_pages(total, page_size),
    )


async def list_user_loans(
    session: AsyncSession,
    user_id: int,
    page: int,
    page_size: int,
    loan_filter: UserLoanFilter = UserLoanFilter.all,
) -> Page[LoanRead]:
    if await session.get(User, user_id) is None:
        raise NotFoundError("Usuário não encontrado.")

    base = select(Loan).where(Loan.user_id == user_id).order_by(Loan.id.desc())
    base = _apply_user_loan_filter(base, loan_filter)
    count_q = select(func.count()).select_from(Loan).where(Loan.user_id == user_id)
    count_q = _apply_user_loan_filter(count_q, loan_filter)

    rows, total = await paginate_selection(session, base, count_q, page, page_size)
    book_ids = {loan.book_id for loan in rows}
    books_by_id = await _books_by_ids(session, book_ids)
    return Page[LoanRead](
        items=[_loan_read_with_book(loan, books_by_id.get(loan.book_id)) for loan in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=total_pages(total, page_size),
    )


async def list_loans_global(
    session: AsyncSession,
    page: int,
    page_size: int,
    loan_filter: LoanListFilter,
) -> Page[LoanRead]:
    now_dt = datetime.now(timezone.utc)
    base = select(Loan).order_by(Loan.id.desc())
    count_base = select(func.count()).select_from(Loan)

    if loan_filter == LoanListFilter.active:
        base = base.where(Loan.returned_at.is_(None))
        count_base = count_base.where(Loan.returned_at.is_(None))
    elif loan_filter == LoanListFilter.overdue:
        base = base.where(Loan.returned_at.is_(None), Loan.due_at < now_dt)
        count_base = count_base.where(Loan.returned_at.is_(None), Loan.due_at < now_dt)

    rows, total = await paginate_selection(session, base, count_base, page, page_size)
    book_ids = {loan.book_id for loan in rows}
    books_by_id = await _books_by_ids(session, book_ids)
    return Page[LoanRead](
        items=[_loan_read_with_book(loan, books_by_id.get(loan.book_id)) for loan in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=total_pages(total, page_size),
    )
