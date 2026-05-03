from typing import Annotated

from fastapi import APIRouter, Depends, Query
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.api.deps import get_current_admin, get_db, get_redis
from app.models import User
from app.schemas.author import AuthorCreate, AuthorRead, AuthorUpdate
from app.schemas.common import Page
from app.services import author_service

router = APIRouter(prefix="/authors", tags=["Authors"])


@router.get("", response_model=Page[AuthorRead])
async def list_authors(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    q: str | None = Query(None, max_length=200, description="Filter by name or bio (case-insensitive)."),
) -> Page[AuthorRead]:
    """List authors (needed to obtain `author_id` when creating books)."""
    return await author_service.list_authors(db, page, page_size, q)


@router.post("", response_model=AuthorRead, status_code=201)
async def create_author(
    data: AuthorCreate,
    _admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis | None, Depends(get_redis)],
) -> AuthorRead:
    """Create an author (admin only)."""
    return await author_service.create_author(db, data, redis)


@router.patch("/{author_id}", response_model=AuthorRead)
async def update_author(
    author_id: int,
    data: AuthorUpdate,
    _admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis | None, Depends(get_redis)],
) -> AuthorRead:
    """Partially update an author (`name`, `bio`). Admin only."""
    return await author_service.update_author(db, author_id, data, redis)


@router.delete("/{author_id}", status_code=204)
async def delete_author(
    author_id: int,
    _admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis | None, Depends(get_redis)],
) -> Response:
    """Delete an author with no linked books. Admin only."""
    await author_service.delete_author(db, author_id, redis)
    return Response(status_code=204)
