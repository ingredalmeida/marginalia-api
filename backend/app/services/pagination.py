from math import ceil
from typing import Any, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


async def paginate_selection(
    session: AsyncSession,
    base_query: Select[tuple[T]],
    count_query: Select,
    page: int,
    page_size: int,
) -> tuple[list[T], int]:
    total = (await session.scalar(count_query)) or 0
    offset = (page - 1) * page_size
    result = await session.execute(base_query.offset(offset).limit(page_size))
    items = list[Any](result.scalars().all())
    return items, total


def total_pages(total: int, page_size: int) -> int:
    if total == 0:
        return 0
    return ceil(total / page_size)
