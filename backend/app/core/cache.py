"""Redis cache keys and invalidation for book catalog reads."""

import asyncio
import logging

from redis import Redis
from redis.exceptions import RedisError

BOOK_PREFIX = "lb:book:"
LIST_PREFIX = "lb:books:"


def book_detail_key(book_id: int) -> str:
    return f"{BOOK_PREFIX}{book_id}"


def books_list_key(page: int, page_size: int) -> str:
    return f"{LIST_PREFIX}p{page}:s{page_size}"


def invalidate_book_catalog_cache(redis: Redis | None) -> None:
    if redis is None:
        return
    for key in redis.scan_iter(f"{BOOK_PREFIX}*"):
        redis.delete(key)
    for key in redis.scan_iter(f"{LIST_PREFIX}*"):
        redis.delete(key)


_log = logging.getLogger(__name__)


async def invalidate_book_catalog_cache_async(redis: Redis | None) -> None:
    """Non-blocking wrapper for async request handlers."""
    if redis is None:
        return
    try:
        await asyncio.to_thread(invalidate_book_catalog_cache, redis)
    except (RedisError, OSError) as e:
        _log.warning("book_catalog_cache_invalidation_failed: %s", e)
