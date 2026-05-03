from collections.abc import AsyncGenerator
from typing import Annotated

import structlog
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AuthError, ForbiddenError
from app.core.security import decode_token
from app.models import User

_bearer = HTTPBearer(auto_error=False)


async def bind_correlation_context(request: Request) -> AsyncGenerator[None, None]:
    """Bind correlation_id for structlog in async route handlers."""
    cid = getattr(request.state, "correlation_id", None)
    if cid:
        structlog.contextvars.bind_contextvars(correlation_id=cid)
    try:
        yield
    finally:
        structlog.contextvars.clear_contextvars()


def get_redis(request: Request) -> Redis | None:
    return getattr(request.app.state, "redis", None)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthError("Not authenticated.")
    try:
        user_id = decode_token(credentials.credentials)
    except ValueError:
        raise AuthError("Invalid or expired token.") from None
    user = await db.get(User, user_id)
    if user is None:
        raise AuthError("User not found.")
    return user


async def get_current_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not user.is_admin:
        raise ForbiddenError("Admin privileges required.")
    return user
