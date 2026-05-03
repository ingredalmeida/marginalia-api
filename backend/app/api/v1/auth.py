from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi.util import get_remote_address

from app.api.deps import get_db
from app.core.rate_limit import limiter
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserRead
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserRead, status_code=201)
@limiter.limit("10/minute", key_func=get_remote_address)
async def register(
    request: Request,
    data: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserRead:
    """Create a patron account (password stored as bcrypt hash)."""
    return await auth_service.register(db, data)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("30/minute", key_func=get_remote_address)
async def login(
    request: Request,
    data: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Exchange email and password for a JWT access token."""
    return await auth_service.login(db, str(data.email), data.password)
