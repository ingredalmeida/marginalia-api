from datetime import datetime, timedelta, timezone

from redis import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.cache import invalidate_book_catalog_cache_async
from app.core.constants import (
    LOAN_DEFAULT_DAYS,
    MAX_ACTIVE_LOANS_PER_USER,
    MAX_PENDING_RESERVATIONS_PER_USER,
    RESERVATION_HOLD_NOTIFICATION_DEADLINE_COPY,
    reservation_hold_timedelta,
)
from app.core.exceptions import ConflictError, DomainError, ForbiddenError, NotFoundError
from app.models import Book, Loan, Reservation, User
from app.schemas.common import Page
from app.schemas.reservation import ReservationRead
from app.services.book_service import active_loan_book_ids
from app.services.pagination import paginate_selection, total_pages

PENDING = "pending"
FULFILLED = "fulfilled"
CANCELLED = "cancelled"
HOLD = "hold"
NOTIFICATION_KIND_RESERVATION_HOLD = "reservation_hold"


def _reservation_read(
    r: Reservation,
    *,
    book_title: str | None = None,
    author_name: str | None = None,
    queue_position: int | None = None,
) -> ReservationRead:
    return ReservationRead(
        id=r.id,
        user_id=r.user_id,
        book_id=r.book_id,
        status=r.status,
        created_at=r.created_at,
        hold_until=r.hold_until,
        book_title=book_title,
        author_name=author_name,
        queue_position=queue_position,
    )


async def _books_by_ids(session: AsyncSession, book_ids: set[int]) -> dict[int, Book]:
    if not book_ids:
        return {}
    result = await session.execute(
        select(Book).options(selectinload(Book.author)).where(Book.id.in_(book_ids))
    )
    return {b.id: b for b in result.scalars().unique().all()}


async def _active_loan_count(session: AsyncSession, user_id: int) -> int:
    q = select(func.count()).select_from(Loan).where(
        Loan.user_id == user_id,
        Loan.returned_at.is_(None),
    )
    return int((await session.scalar(q)) or 0)


async def _count_user_pending_reservations(session: AsyncSession, user_id: int) -> int:
    n = await session.scalar(
        select(func.count()).select_from(Reservation).where(
            Reservation.user_id == user_id,
            Reservation.status.in_((PENDING, HOLD)),
        )
    )
    return int(n or 0)


async def _book_has_active_hold(session: AsyncSession, book_id: int) -> bool:
    n = await session.scalar(
        select(func.count()).select_from(Reservation).where(
            Reservation.book_id == book_id,
            Reservation.status == HOLD,
        )
    )
    return int(n or 0) > 0


async def _queue_positions_for_reservation_ids(
    session: AsyncSession, reservation_ids: list[int]
) -> dict[int, int]:
    if not reservation_ids:
        return {}
    subq = (
        select(
            Reservation.id.label("res_id"),
            func.row_number()
            .over(
                partition_by=Reservation.book_id,
                order_by=(Reservation.created_at.asc(), Reservation.id.asc()),
            )
            .label("queue_position"),
        )
        .where(Reservation.status.in_((PENDING, HOLD)))
        .subquery()
    )
    result = await session.execute(
        select(subq.c.res_id, subq.c.queue_position).where(subq.c.res_id.in_(reservation_ids))
    )
    return {int(row.res_id): int(row.queue_position) for row in result.all()}


async def first_pending_user_id(session: AsyncSession, book_id: int) -> int | None:
    result = await session.execute(
        select(Reservation)
        .where(Reservation.book_id == book_id, Reservation.status == PENDING)
        .order_by(Reservation.created_at.asc(), Reservation.id.asc())
        .limit(1)
    )
    row = result.scalar_one_or_none()
    return row.user_id if row else None


async def assert_borrower_matches_waitlist(
    session: AsyncSession, book_id: int, user_id: int
) -> None:
    result = await session.execute(
        select(Reservation)
        .where(
            Reservation.book_id == book_id,
            Reservation.status.in_((PENDING, HOLD)),
        )
        .order_by(Reservation.created_at.asc(), Reservation.id.asc())
        .limit(1)
    )
    head = result.scalar_one_or_none()
    if head is None:
        return
    if head.user_id != user_id:
        raise ConflictError(
            "Este exemplar tem fila de espera: só a primeira pessoa na fila pode emprestá-lo agora."
        )
    if (
        head.status == HOLD
        and head.hold_until is not None
        and head.hold_until < datetime.now(timezone.utc)
    ):
        raise ConflictError(
            "O prazo da sua reserva encerrou; o exemplar não está mais reservado para você."
        )


async def fulfill_head_reservation_if_matches(
    session: AsyncSession, book_id: int, user_id: int
) -> None:
    result = await session.execute(
        select(Reservation)
        .where(
            Reservation.book_id == book_id,
            Reservation.status.in_((PENDING, HOLD)),
        )
        .order_by(Reservation.created_at.asc(), Reservation.id.asc())
        .limit(1)
    )
    head = result.scalar_one_or_none()
    if head is not None and head.user_id == user_id:
        head.status = FULFILLED
        head.hold_until = None


async def process_book_after_return(
    session: AsyncSession, book_id: int, redis: Redis | None = None
) -> None:
    """After a copy is returned: assign auto-loan to head of queue, or hold if patron is at loan limit."""
    from app.services import notification_service

    head_row = await session.execute(
        select(Reservation)
        .where(
            Reservation.book_id == book_id,
            Reservation.status == PENDING,
        )
        .order_by(Reservation.created_at.asc(), Reservation.id.asc())
        .limit(1)
    )
    head = head_row.scalar_one_or_none()
    if head is None:
        return

    uid = head.user_id
    if await _active_loan_count(session, uid) >= MAX_ACTIVE_LOANS_PER_USER:
        head.status = HOLD
        head.hold_until = datetime.now(timezone.utc) + reservation_hold_timedelta()
        book = await session.get(Book, book_id)
        title = book.title if book else "este título"
        await notification_service.create_notification(
            session,
            uid,
            "Sua reserva: libere um lugar na estante",
            f"«{title}» foi devolvido, mas você já tem {MAX_ACTIVE_LOANS_PER_USER} empréstimos ativos. "
            f"Você tem {RESERVATION_HOLD_NOTIFICATION_DEADLINE_COPY} para devolver um dos seus exemplares e liberar vaga. "
            "Assim que houver vaga, o empréstimo deste título é feito automaticamente. "
            "Se o prazo acabar sem que você libere espaço, a vez passa para a próxima pessoa na fila.",
            kind=NOTIFICATION_KIND_RESERVATION_HOLD,
            ref_reservation_id=head.id,
        )
        await session.flush()
        await invalidate_book_catalog_cache_async(redis)
        return

    now = datetime.now(timezone.utc)
    due = now + timedelta(days=LOAN_DEFAULT_DAYS)
    loan = Loan(
        user_id=uid,
        book_id=book_id,
        borrowed_at=now,
        due_at=due,
        returned_at=None,
        fine_amount=None,
    )
    session.add(loan)
    head.status = FULFILLED
    head.hold_until = None
    book = await session.get(Book, book_id)
    title = book.title if book else "O exemplar"
    await notification_service.create_notification(
        session,
        uid,
        "Empréstimo automático (reserva)",
        f"«{title}» foi emprestado para você porque você era o próximo na fila "
        f"(prazo de devolução: {LOAN_DEFAULT_DAYS} dias).",
        kind="loan_from_reservation",
    )
    await session.flush()
    await invalidate_book_catalog_cache_async(redis)


async def _grant_loan_for_hold(
    session: AsyncSession,
    hold: Reservation,
    redis: Redis | None,
    *,
    title: str,
    body: str,
    kind: str,
) -> None:
    from app.services import notification_service as ns

    now = datetime.now(timezone.utc)
    busy = await active_loan_book_ids(session)
    if hold.book_id in busy:
        raise ConflictError("Este exemplar já está emprestado.")
    due = now + timedelta(days=LOAN_DEFAULT_DAYS)
    loan = Loan(
        user_id=hold.user_id,
        book_id=hold.book_id,
        borrowed_at=now,
        due_at=due,
        returned_at=None,
        fine_amount=None,
    )
    session.add(loan)
    hold.status = FULFILLED
    hold.hold_until = None
    await ns.create_notification(session, hold.user_id, title, body, kind)
    await session.flush()
    await invalidate_book_catalog_cache_async(redis)


async def _cancel_hold_and_advance(
    session: AsyncSession, hold: Reservation, redis: Redis | None
) -> None:
    book_id = hold.book_id
    hold.status = CANCELLED
    hold.hold_until = None
    await session.flush()
    await process_book_after_return(session, book_id, redis)


async def try_fulfill_user_holds_after_slot_freed(
    session: AsyncSession, user_id: int, redis: Redis | None = None
) -> None:
    """When someone frees a loan slot, promote any active holds into loans if possible."""
    # Sem Celery em dev, holds expirados ficam na BD; converger antes de tentar emprestar.
    await expire_expired_reservation_holds(session, redis)

    now = datetime.now(timezone.utc)
    while await _active_loan_count(session, user_id) < MAX_ACTIVE_LOANS_PER_USER:
        res = await session.execute(
            select(Reservation)
            .where(
                Reservation.user_id == user_id,
                Reservation.status == HOLD,
            )
            .order_by(Reservation.hold_until.asc(), Reservation.id.asc())
            .limit(1)
        )
        hold = res.scalar_one_or_none()
        if hold is None:
            return
        if hold.hold_until is not None and hold.hold_until < now:
            # Ainda expirado (janela rara): cancela e segue; não retornar cedo (isso deixava o hold preso).
            await _cancel_hold_and_advance(session, hold, redis)
            continue

        busy = await active_loan_book_ids(session)
        if hold.book_id in busy:
            return

        book = await session.get(Book, hold.book_id)
        title = book.title if book else "O exemplar"
        await _grant_loan_for_hold(
            session,
            hold,
            redis,
            title="Reserva confirmada",
            body=f"Você liberou um lugar na estante; «{title}» foi emprestado conforme sua reserva.",
            kind="hold_fulfilled_after_return",
        )


async def expire_expired_reservation_holds(
    session: AsyncSession, redis: Redis | None = None
) -> int:
    """Cancel holds past deadline and offer the copy to the next waiter."""
    from app.services import notification_service

    now = datetime.now(timezone.utc)
    result = await session.execute(
        select(Reservation).where(
            Reservation.status == HOLD,
            Reservation.hold_until.is_not(None),
            Reservation.hold_until < now,
        )
    )
    rows = list(result.scalars().all())
    n_done = 0
    for row in rows:
        book_id = row.book_id
        uid = row.user_id
        row.status = CANCELLED
        row.hold_until = None

        await notification_service.create_notification(
            session,
            uid,
            "Prazo da reserva encerrado",
            f"O prazo ({RESERVATION_HOLD_NOTIFICATION_DEADLINE_COPY}) para liberar vaga na estante acabou sem "
            "devolução; o exemplar será oferecido ao próximo na fila ou liberado.",
            kind="hold_expired",
        )
        await session.flush()
        await process_book_after_return(session, book_id, redis)
        n_done += 1
    return n_done


async def create_reservation(
    session: AsyncSession, user_id: int, book_id: int, redis: Redis | None = None
) -> ReservationRead:
    if await session.get(User, user_id) is None:
        raise NotFoundError("Usuário não encontrado.")
    if await session.get(Book, book_id) is None:
        raise NotFoundError("Livro não encontrado.")

    if await _book_has_active_hold(session, book_id):
        raise ConflictError(
            "Outra pessoa tem prioridade de retirada neste exemplar (reserva com prazo). "
            "Aguarde ou escolha outro título."
        )

    busy = await active_loan_book_ids(session)
    if book_id not in busy:
        raise ConflictError(
            "A fila de reserva só existe enquanto o exemplar está emprestado. Ele já está disponível para empréstimo."
        )

    result = await session.execute(
        select(Reservation).where(
            Reservation.user_id == user_id,
            Reservation.book_id == book_id,
            Reservation.status.in_((PENDING, HOLD)),
        )
    )
    dup = result.scalar_one_or_none()
    if dup is not None:
        raise ConflictError("Você já está na fila de espera deste exemplar.")

    if await _count_user_pending_reservations(session, user_id) >= MAX_PENDING_RESERVATIONS_PER_USER:
        raise ConflictError(
            f"Você já tem {MAX_PENDING_RESERVATIONS_PER_USER} reservas na fila (limite do sistema). "
            "Cancele uma reserva ou aguarde uma ser atendida para entrar em outra fila."
        )

    r = Reservation(user_id=user_id, book_id=book_id, status=PENDING)
    session.add(r)
    await session.commit()
    await session.refresh(r)
    await invalidate_book_catalog_cache_async(redis)
    books_by_id = await _books_by_ids(session, {book_id})
    b = books_by_id.get(book_id)
    author_name = b.author.name if b is not None and b.author is not None else None
    pos_map = await _queue_positions_for_reservation_ids(session, [r.id])
    return _reservation_read(
        r,
        book_title=b.title if b is not None else None,
        author_name=author_name,
        queue_position=pos_map.get(r.id),
    )


async def cancel_reservation(
    session: AsyncSession,
    reservation_id: int,
    acting_user_id: int,
    acting_is_admin: bool,
    redis: Redis | None = None,
) -> None:
    r = await session.get(Reservation, reservation_id)
    if r is None:
        raise NotFoundError("Reserva não encontrada.")
    if r.status not in (PENDING, HOLD):
        raise DomainError("Esta reserva não está mais ativa.")
    if not acting_is_admin and r.user_id != acting_user_id:
        raise ForbiddenError("Só é possível cancelar suas próprias reservas.")
    book_id = r.book_id
    was_hold = r.status == HOLD
    r.status = CANCELLED
    r.hold_until = None
    await session.flush()
    if was_hold:
        await process_book_after_return(session, book_id, redis)
    await session.commit()
    await invalidate_book_catalog_cache_async(redis)


async def list_reservations_for_book(
    session: AsyncSession, book_id: int, page: int, page_size: int
) -> Page[ReservationRead]:
    if await session.get(Book, book_id) is None:
        raise NotFoundError("Livro não encontrado.")
    base = (
        select(Reservation)
        .where(
            Reservation.book_id == book_id,
            Reservation.status.in_((PENDING, HOLD)),
        )
        .order_by(Reservation.created_at.asc(), Reservation.id.asc())
    )
    count_q = select(func.count()).select_from(Reservation).where(
        Reservation.book_id == book_id,
        Reservation.status.in_((PENDING, HOLD)),
    )
    rows, total = await paginate_selection(session, base, count_q, page, page_size)
    book_result = await session.execute(
        select(Book).options(selectinload(Book.author)).where(Book.id == book_id)
    )
    book = book_result.scalar_one_or_none()
    book_title = book.title if book is not None else None
    author_name = book.author.name if book is not None and book.author is not None else None
    items = [
        _reservation_read(
            x,
            book_title=book_title,
            author_name=author_name,
            queue_position=(page - 1) * page_size + idx + 1,
        )
        for idx, x in enumerate(rows)
    ]
    return Page[ReservationRead](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=total_pages(total, page_size),
    )


async def list_my_pending_reservations(
    session: AsyncSession, user_id: int, page: int, page_size: int
) -> Page[ReservationRead]:
    base = (
        select(Reservation)
        .where(
            Reservation.user_id == user_id,
            Reservation.status.in_((PENDING, HOLD)),
        )
        .order_by(Reservation.created_at.desc(), Reservation.id.desc())
    )
    count_q = select(func.count()).select_from(Reservation).where(
        Reservation.user_id == user_id,
        Reservation.status.in_((PENDING, HOLD)),
    )
    rows, total = await paginate_selection(session, base, count_q, page, page_size)
    ids = [x.id for x in rows]
    pos_map = await _queue_positions_for_reservation_ids(session, ids)
    book_ids = {x.book_id for x in rows}
    books_by_id = await _books_by_ids(session, book_ids)
    items = []
    for r in rows:
        b = books_by_id.get(r.book_id)
        bt = b.title if b is not None else None
        an = b.author.name if b is not None and b.author is not None else None
        items.append(
            _reservation_read(
                r,
                book_title=bt,
                author_name=an,
                queue_position=pos_map.get(r.id),
            )
        )
    return Page[ReservationRead](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=total_pages(total, page_size),
    )
