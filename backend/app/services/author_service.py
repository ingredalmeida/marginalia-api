from redis import Redis
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import invalidate_book_catalog_cache_async
from app.core.exceptions import ConflictError, DomainError, NotFoundError
from app.models import Author, Book
from app.schemas.author import AuthorCreate, AuthorRead, AuthorUpdate
from app.schemas.common import Page
from app.services.pagination import paginate_selection, total_pages


async def create_author(
    session: AsyncSession, data: AuthorCreate, redis: Redis | None = None
) -> AuthorRead:
    author = Author(name=data.name, bio=data.bio)
    session.add(author)
    await session.commit()
    await session.refresh(author)
    await invalidate_book_catalog_cache_async(redis)
    return AuthorRead.model_validate(author)


async def get_author(session: AsyncSession, author_id: int) -> Author:
    author = await session.get(Author, author_id)
    if author is None:
        raise NotFoundError("Author not found.")
    return author


async def delete_author(
    session: AsyncSession, author_id: int, redis: Redis | None = None
) -> None:
    author = await session.get(Author, author_id)
    if author is None:
        raise NotFoundError("Author not found.")
    n = await session.scalar(
        select(func.count()).select_from(Book).where(Book.author_id == author_id)
    )
    if (n or 0) > 0:
        raise ConflictError("Cannot delete author while books reference this author.")
    await session.delete(author)
    await session.commit()
    await invalidate_book_catalog_cache_async(redis)


async def update_author(
    session: AsyncSession, author_id: int, data: AuthorUpdate, redis: Redis | None = None
) -> AuthorRead:
    author = await get_author(session, author_id)
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        raise DomainError("No fields to update.")
    for key, value in updates.items():
        setattr(author, key, value)
    await session.commit()
    await session.refresh(author)
    await invalidate_book_catalog_cache_async(redis)
    return AuthorRead.model_validate(author)


async def list_authors(
    session: AsyncSession, page: int, page_size: int, search: str | None = None
) -> Page[AuthorRead]:
    base = select(Author).order_by(Author.id)
    count_q = select(func.count()).select_from(Author)
    if search and search.strip():
        term = f"%{search.strip()}%"
        filt = or_(Author.name.ilike(term), Author.bio.ilike(term))
        base = base.where(filt)
        count_q = count_q.where(filt)
    rows, total = await paginate_selection(session, base, count_q, page, page_size)
    return Page[AuthorRead](
        items=[AuthorRead.model_validate(a) for a in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=total_pages(total, page_size),
    )
