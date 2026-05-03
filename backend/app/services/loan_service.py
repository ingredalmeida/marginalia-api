from datetime import datetime, timedelta, timezone
from decimal import Decimal

import structlog
from redis import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import invalidate_book_catalog_cache_async
from app.core.constants import (
    FINE_PER_OVERDUE_DAY,
    LOAN_DEFAULT_DAYS,
    MAX_ACTIVE_LOANS_PER_USER,
    MAX_LOAN_RENEWALS,
    RENEWAL_EXTRA_DAYS,
    RENEWAL_REQUEST_CALENDAR_DAY_LIMIT,
)
from app.core.exceptions import ConflictError, DomainError, ForbiddenError, NotFoundError
from app.models import Book, Loan, User
from app.schemas.loan import LoanCreate, LoanRead, LoanReturnResult
from app.services.book_service import active_loan_book_ids
from app.services import reservation_service

log = structlog.get_logger(__name__)


def _log_context() -> dict:
    return dict(structlog.contextvars.get_contextvars())


def _calendar_days_since_borrow(borrowed_at: datetime, now: datetime) -> int:
    b = borrowed_at if borrowed_at.tzinfo else borrowed_at.replace(tzinfo=timezone.utc)
    n = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
    return (n.date() - b.date()).days


async def _count_active_user_loans(session: AsyncSession, user_id: int) -> int:
    q = select(func.count()).select_from(Loan).where(
        Loan.user_id == user_id,
        Loan.returned_at.is_(None),
    )
    return (await session.scalar(q)) or 0


async def create_loan(
    session: AsyncSession, data: LoanCreate, redis: Redis | None = None
) -> LoanRead:
    if await session.get(User, data.user_id) is None:
        raise NotFoundError("Usuário não encontrado.")
    if await session.get(Book, data.book_id) is None:
        raise NotFoundError("Livro não encontrado.")

    if await _count_active_user_loans(session, data.user_id) >= MAX_ACTIVE_LOANS_PER_USER:
        raise ConflictError(
            f"Você já tem {MAX_ACTIVE_LOANS_PER_USER} empréstimos ativos (limite do sistema). "
            "Devolva um exemplar para poder pegar outro."
        )

    busy = await active_loan_book_ids(session)
    if data.book_id in busy:
        raise ConflictError("Este exemplar já está emprestado.")

    await reservation_service.assert_borrower_matches_waitlist(
        session, data.book_id, data.user_id
    )

    now = datetime.now(timezone.utc)
    due = now + timedelta(days=LOAN_DEFAULT_DAYS)
    loan = Loan(
        user_id=data.user_id,
        book_id=data.book_id,
        borrowed_at=now,
        due_at=due,
        returned_at=None,
        fine_amount=None,
    )
    session.add(loan)
    await reservation_service.fulfill_head_reservation_if_matches(
        session, data.book_id, data.user_id
    )
    await session.commit()
    await session.refresh(loan)
    await invalidate_book_catalog_cache_async(redis)
    log.info(
        "loan_created",
        **_log_context(),
        loan_id=loan.id,
        user_id=loan.user_id,
        book_id=loan.book_id,
        due_at=loan.due_at.isoformat(),
    )
    return LoanRead.model_validate(loan)


async def return_loan(
    session: AsyncSession,
    loan_id: int,
    redis: Redis | None = None,
    *,
    acting_user_id: int,
    acting_is_admin: bool = False,
) -> LoanReturnResult:
    loan = await session.get(Loan, loan_id)
    if loan is None:
        raise NotFoundError("Empréstimo não encontrado.")
    if not acting_is_admin and loan.user_id != acting_user_id:
        raise ForbiddenError("Só é possível registrar devolução do seu próprio empréstimo.")
    if loan.returned_at is not None:
        raise DomainError("Este empréstimo já foi devolvido.")

    now = datetime.now(timezone.utc)
    due_date = loan.due_at.date()
    return_date = now.date()
    overdue_days = max(0, (return_date - due_date).days)
    fine = Decimal(overdue_days) * FINE_PER_OVERDUE_DAY

    loan.returned_at = now
    loan.fine_amount = fine
    await session.flush()
    await reservation_service.process_book_after_return(session, loan.book_id, redis)
    await reservation_service.try_fulfill_user_holds_after_slot_freed(session, loan.user_id, redis)
    await session.commit()
    await session.refresh(loan)
    await invalidate_book_catalog_cache_async(redis)
    log.info(
        "loan_returned",
        **_log_context(),
        loan_id=loan.id,
        user_id=loan.user_id,
        book_id=loan.book_id,
        overdue_days=overdue_days,
        fine_amount=str(fine),
    )
    return LoanReturnResult(loan=LoanRead.model_validate(loan), fine_amount=fine)


async def renew_loan(
    session: AsyncSession,
    loan_id: int,
    redis: Redis | None = None,
    *,
    acting_user_id: int,
    acting_is_admin: bool = False,
) -> LoanRead:
    loan = await session.get(Loan, loan_id)
    if loan is None:
        raise NotFoundError("Empréstimo não encontrado.")
    if not acting_is_admin and loan.user_id != acting_user_id:
        raise ForbiddenError("Só é possível renovar o seu próprio empréstimo.")
    if loan.returned_at is not None:
        raise DomainError("Não é possível renovar um empréstimo já encerrado.")

    now = datetime.now(timezone.utc)
    due = loan.due_at
    if due.tzinfo is None:
        due = due.replace(tzinfo=timezone.utc)
    if now > due:
        raise DomainError("Não é possível renovar com devolução em atraso. Devolva o exemplar primeiro.")

    if loan.renewal_count >= MAX_LOAN_RENEWALS:
        raise ConflictError(
            f"Este empréstimo já foi renovado o máximo permitido ({MAX_LOAN_RENEWALS} vez(es))."
        )

    if (
        _calendar_days_since_borrow(loan.borrowed_at, now)
        >= RENEWAL_REQUEST_CALENDAR_DAY_LIMIT
    ):
        raise DomainError(
            f"A renovação só pode ser pedida nos primeiros {RENEWAL_REQUEST_CALENDAR_DAY_LIMIT} "
            "dias corridos após a retirada."
        )

    if await reservation_service.first_pending_user_id(session, loan.book_id) is not None:
        raise ConflictError(
            "Não é possível renovar enquanto houver fila de espera para este exemplar; devolva-o para "
            "que a próxima pessoa possa emprestar."
        )

    loan.due_at = due + timedelta(days=RENEWAL_EXTRA_DAYS)
    loan.renewal_count = loan.renewal_count + 1
    await session.commit()
    await session.refresh(loan)
    await invalidate_book_catalog_cache_async(redis)
    log.info(
        "loan_renewed",
        **_log_context(),
        loan_id=loan.id,
        user_id=loan.user_id,
        book_id=loan.book_id,
        due_at=loan.due_at.isoformat(),
        renewal_count=loan.renewal_count,
    )
    return LoanRead.model_validate(loan)
