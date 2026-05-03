from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_redis
from app.core.exceptions import ForbiddenError
from app.models import User
from app.schemas.common import Page
from app.schemas.reservation import ReservationCreate, ReservationRead
from app.services import reservation_service

router = APIRouter(prefix="/reservations", tags=["Reservations"])


@router.post("", response_model=ReservationRead, status_code=201)
async def create_reservation(
    data: ReservationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis | None, Depends(get_redis)],
    current: Annotated[User, Depends(get_current_user)],
) -> ReservationRead:
    """Join the waitlist for a copy (only while it is on loan)."""
    if not current.is_admin and data.user_id != current.id:
        raise ForbiddenError("Você só pode criar reservas para si mesma(o).")
    return await reservation_service.create_reservation(db, data.user_id, data.book_id, redis)


@router.get("", response_model=Page[ReservationRead])
async def list_reservations(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    book_id: int | None = Query(
        None,
        description="If set, list pending queue for this book (FIFO). Otherwise list your pending reservations.",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
) -> Page[ReservationRead]:
    if book_id is not None:
        return await reservation_service.list_reservations_for_book(db, book_id, page, page_size)
    return await reservation_service.list_my_pending_reservations(db, current.id, page, page_size)


@router.delete("/{reservation_id}", status_code=204)
async def cancel_reservation(
    reservation_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis | None, Depends(get_redis)],
    current: Annotated[User, Depends(get_current_user)],
) -> Response:
    await reservation_service.cancel_reservation(
        db,
        reservation_id,
        acting_user_id=current.id,
        acting_is_admin=current.is_admin,
        redis=redis,
    )
    return Response(status_code=204)
