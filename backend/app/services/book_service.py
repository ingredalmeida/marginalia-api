import asyncio
import json

from pydantic import TypeAdapter
from redis import Redis
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.core.cache import book_detail_key, books_list_key, invalidate_book_catalog_cache_async
from app.core.exceptions import ConflictError, DomainError, NotFoundError
from app.models import Author, Book, Loan, Reservation
from app.schemas.book import BookAvailability, BookCreate, BookRead, BookUpdate
from app.schemas.common import Page
from app.services.author_service import get_author
from app.services.pagination import paginate_selection, total_pages

_page_book_adapter: TypeAdapter = TypeAdapter(Page[BookRead])


async def active_loan_book_ids(session: AsyncSession) -> set[int]:
    q = select(Loan.book_id).where(Loan.returned_at.is_(None)).distinct()
    result = await session.execute(q)
    return set(result.scalars().all())


async def book_ids_with_reservation_hold(session: AsyncSession) -> set[int]:
    """Copies locked for the patron at the head of the queue (awaiting slot / hour window)."""
    q = select(Reservation.book_id).where(Reservation.status == "hold").distinct()
    result = await session.execute(q)
    return set(result.scalars().all())


async def create_book(
    session: AsyncSession, data: BookCreate, redis: Redis | None = None
) -> BookRead:
    await get_author(session, data.author_id)
    book = Book(
        title=data.title,
        author_id=data.author_id,
        description=data.description,
        publisher=data.publisher,
        isbn=data.isbn,
        publication_year=data.publication_year,
    )
    session.add(book)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise ConflictError("ISBN already registered for another book.") from None
    await session.refresh(book)
    await invalidate_book_catalog_cache_async(redis)
    return await get_book(session, book.id, redis)


async def delete_book(
    session: AsyncSession, book_id: int, redis: Redis | None = None
) -> None:
    book = await session.get(Book, book_id)
    if book is None:
        raise NotFoundError("Book not found.")
    n = await session.scalar(
        select(func.count()).select_from(Loan).where(Loan.book_id == book_id)
    )
    if (n or 0) > 0:
        raise ConflictError("Cannot delete book with existing loans.")
    await session.delete(book)
    await session.commit()
    await invalidate_book_catalog_cache_async(redis)


async def update_book(
    session: AsyncSession, book_id: int, data: BookUpdate, redis: Redis | None = None
) -> BookRead:
    result = await session.execute(
        select(Book).options(joinedload(Book.author)).where(Book.id == book_id)
    )
    book = result.unique().scalar_one_or_none()
    if book is None:
        raise NotFoundError("Book not found.")
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        raise DomainError("No fields to update.")
    if "author_id" in updates:
        await get_author(session, updates["author_id"])
    for key, value in updates.items():
        setattr(book, key, value)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise ConflictError("ISBN already registered for another book.") from None
    await session.refresh(book)
    await invalidate_book_catalog_cache_async(redis)
    return await get_book(session, book.id, redis)


def _ilike_search_pattern(raw: str) -> str:
    """Escape SQL LIKE wildcards so "%" and "_" are matched literally when intended."""
    return (
        raw.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


async def get_book(
    session: AsyncSession, book_id: int, redis: Redis | None = None
) -> BookRead:
    cache_key = book_detail_key(book_id)
    if redis is not None:
        cached = await asyncio.to_thread(redis.get, cache_key)
        if cached:
            data = json.loads(cached)
            return BookRead.model_validate(data)

    result = await session.execute(
        select(Book).options(joinedload(Book.author)).where(Book.id == book_id)
    )
    book = result.unique().scalar_one_or_none()
    if book is None:
        raise NotFoundError("Book not found.")
    busy = await active_loan_book_ids(session)
    held = await book_ids_with_reservation_hold(session)
    available = book.id not in busy and book.id not in held
    out = BookRead.model_validate(book).model_copy(update={"available": available})
    if redis is not None:
        await asyncio.to_thread(
            redis.setex,
            cache_key,
            settings.cache_ttl_book_seconds,
            out.model_dump_json(),
        )
    return out


async def list_books(
    session: AsyncSession,
    page: int,
    page_size: int,
    redis: Redis | None = None,
    search: str | None = None,
) -> Page[BookRead]:
    search_trim = search.strip() if search else ""
    use_list_cache = redis is not None and not search_trim
    cache_key = books_list_key(page, page_size) if use_list_cache else None
    if use_list_cache and cache_key is not None:
        cached = await asyncio.to_thread(redis.get, cache_key)
        if cached:
            return _page_book_adapter.validate_json(cached)

    if search_trim:
        pat = f"%{_ilike_search_pattern(search_trim)}%"
        filt = or_(
            Book.title.ilike(pat, escape="\\"),
            Author.name.ilike(pat, escape="\\"),
        )
        base = (
            select(Book)
            .options(joinedload(Book.author))
            .join(Author, Book.author_id == Author.id)
            .where(filt)
            .order_by(Book.id)
        )
        count_q = select(func.count()).select_from(Book).join(Author, Book.author_id == Author.id).where(filt)
    else:
        base = select(Book).options(joinedload(Book.author)).order_by(Book.id)
        count_q = select(func.count()).select_from(Book)
    rows, total = await paginate_selection(session, base, count_q, page, page_size)
    busy = await active_loan_book_ids(session)
    held = await book_ids_with_reservation_hold(session)
    items = []
    for b in rows:
        av = b.id not in busy and b.id not in held
        br = BookRead.model_validate(b)
        items.append(br.model_copy(update={"available": av}))
    page_out = Page[BookRead](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=total_pages(total, page_size),
    )
    if use_list_cache and cache_key is not None:
        await asyncio.to_thread(
            redis.setex,
            cache_key,
            settings.cache_ttl_book_list_seconds,
            page_out.model_dump_json(),
        )
    return page_out


async def book_availability(session: AsyncSession, book_id: int) -> BookAvailability:
    if await session.get(Book, book_id) is None:
        raise NotFoundError("Book not found.")
    busy = await active_loan_book_ids(session)
    if book_id in busy:
        return BookAvailability(
            book_id=book_id,
            available=False,
            reason="Copy has an active loan.",
        )
    held = await book_ids_with_reservation_hold(session)
    if book_id in held:
        return BookAvailability(
            book_id=book_id,
            available=False,
            reason="Reservation hold window active.",
        )
    return BookAvailability(book_id=book_id, available=True, reason=None)
