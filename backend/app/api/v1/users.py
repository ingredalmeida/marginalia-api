from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.api.deps import get_current_admin, get_current_user, get_db
from app.core.exceptions import ForbiddenError
from app.models import User
from app.schemas.common import Page
from app.schemas.loan import LoanRead, UserLoanFilter
from app.schemas.user import UserRead, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=Page[UserRead])
async def list_users(
    _admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    q: str | None = Query(None, max_length=200, description="Filter by name or email (case-insensitive)."),
) -> Page[UserRead]:
    """List users with pagination (admin only)."""
    return await user_service.list_users(db, page, page_size, q)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    current: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserRead:
    """Get user by id (self or admin)."""
    if user_id != current.id and not current.is_admin:
        raise ForbiddenError("You may only view your own profile unless you are an admin.")
    return await user_service.get_user(db, user_id)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    data: UserUpdate,
    current: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserRead:
    """Update `name`, `email`, and/or `password` for your own account; admins may update any user."""
    if user_id != current.id and not current.is_admin:
        raise ForbiddenError("You may only update your own profile unless you are an admin.")
    return await user_service.update_user(db, user_id, data)


@router.delete("/{user_id}", status_code=204)
async def remove_user(
    user_id: int,
    _admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    """Delete a user with no loans. Admin only."""
    await user_service.delete_user(db, user_id)
    return Response(status_code=204)


@router.get("/{user_id}/loans", response_model=Page[LoanRead])
async def list_user_loans(
    user_id: int,
    current: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    loan_filter: UserLoanFilter = Query(
        UserLoanFilter.all,
        alias="status",
        description="Filter: `active`, `returned`, `overdue`, or `all`.",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
) -> Page[LoanRead]:
    """List loans for a user (self or admin). Use `status=returned` or `all` for history."""
    if user_id != current.id and not current.is_admin:
        raise ForbiddenError("You may only view your own loans unless you are an admin.")
    return await user_service.list_user_loans(db, user_id, page, page_size, loan_filter)
