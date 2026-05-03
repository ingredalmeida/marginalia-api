from typing import Annotated

from fastapi import APIRouter, Depends, Query
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.api.deps import get_current_admin, get_db, get_redis
from app.models import User
from app.schemas.book import BookAvailability, BookCreate, BookRead, BookUpdate
from app.schemas.common import Page
from app.services import book_service

router = APIRouter(prefix="/books", tags=["Books"])


@router.get("", response_model=Page[BookRead])
async def list_books(
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis | None, Depends(get_redis)],
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    q: str | None = Query(None, max_length=200, description="Filter by title or author name (case-insensitive)."),
    search: str | None = Query(
        None, max_length=200, description="Same as `q` (some clients use this name)."
    ),
) -> Page[BookRead]:
    """List books with nested author and `available` flag."""
    term = (q or search or "").strip() or None
    return await book_service.list_books(db, page, page_size, redis, term)


@router.post("", response_model=BookRead, status_code=201)
async def create_book(
    data: BookCreate,
    _admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis | None, Depends(get_redis)],
) -> BookRead:
    """Create a book linked to an existing author (`author_id`). Admin only."""
    return await book_service.create_book(db, data, redis)


@router.get("/{book_id}", response_model=BookRead)
async def get_book(
    book_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis | None, Depends(get_redis)],
) -> BookRead:
    """Book detail and availability."""
    return await book_service.get_book(db, book_id, redis)


@router.patch("/{book_id}", response_model=BookRead)
async def update_book(
    book_id: int,
    data: BookUpdate,
    _admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis | None, Depends(get_redis)],
) -> BookRead:
    """Partially update a book. Admin only."""
    return await book_service.update_book(db, book_id, data, redis)


@router.delete("/{book_id}", status_code=204)
async def delete_book(
    book_id: int,
    _admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis | None, Depends(get_redis)],
) -> Response:
    """Delete a book that has no loans. Admin only."""
    await book_service.delete_book(db, book_id, redis)
    return Response(status_code=204)


@router.get("/{book_id}/availability", response_model=BookAvailability)
async def get_availability(
    book_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BookAvailability:
    """Check whether the copy is available to borrow."""
    return await book_service.book_availability(db, book_id)
