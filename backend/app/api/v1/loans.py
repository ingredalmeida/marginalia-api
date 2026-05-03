from typing import Annotated

from fastapi import APIRouter, Depends, Query
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_current_user, get_db, get_redis
from app.core.exceptions import ForbiddenError
from app.models import User
from app.schemas.common import Page
from app.schemas.loan import LoanCreate, LoanListFilter, LoanRead, LoanReturnResult
from app.services import loan_service, user_service

router = APIRouter(prefix="/loans", tags=["Loans"])


@router.get("", response_model=Page[LoanRead])
async def list_loans(
    _admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    loan_filter: LoanListFilter = Query(
        LoanListFilter.all,
        alias="filter",
        description="Filter listing: `active`, `overdue`, or `all`.",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
) -> Page[LoanRead]:
    """List all loans (admin only): active, overdue, or full history."""
    return await user_service.list_loans_global(db, page, page_size, loan_filter)


@router.post("", response_model=LoanRead, status_code=201)
async def create_loan(
    data: LoanCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis | None, Depends(get_redis)],
    current: Annotated[User, Depends(get_current_user)],
) -> LoanRead:
    """Borrow a copy (14-day term; max 3 active per user; one active loan per copy)."""
    if not current.is_admin and data.user_id != current.id:
        raise ForbiddenError(
            "Você só pode registrar empréstimo para si mesma(o). Administradoras podem registrar para outras contas."
        )
    return await loan_service.create_loan(db, data, redis)


@router.post("/{loan_id}/return", response_model=LoanReturnResult)
async def return_loan(
    loan_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis | None, Depends(get_redis)],
    current: Annotated[User, Depends(get_current_user)],
) -> LoanReturnResult:
    """Return a copy and compute fine (BRL 2.00 per overdue calendar day after `due_at`)."""
    return await loan_service.return_loan(
        db,
        loan_id,
        redis,
        acting_user_id=current.id,
        acting_is_admin=current.is_admin,
    )


@router.post("/{loan_id}/renew", response_model=LoanRead)
async def renew_loan(
    loan_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis | None, Depends(get_redis)],
    current: Annotated[User, Depends(get_current_user)],
) -> LoanRead:
    """Add 4 days to current `due_at` (once per loan; only in first 7 calendar days on loan; not if overdue or waitlisted)."""
    return await loan_service.renew_loan(
        db,
        loan_id,
        redis,
        acting_user_id=current.id,
        acting_is_admin=current.is_admin,
    )
