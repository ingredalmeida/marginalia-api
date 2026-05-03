from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthError, ConflictError
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas.auth import RegisterRequest, TokenResponse
from app.schemas.user import UserRead


async def register(session: AsyncSession, data: RegisterRequest) -> UserRead:
    user = User(
        name=data.name,
        email=str(data.email).lower(),
        hashed_password=hash_password(data.password),
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise ConflictError("Email already registered.") from None
    await session.refresh(user)
    return UserRead.model_validate(user)


async def login(session: AsyncSession, email: str, password: str) -> TokenResponse:
    result = await session.execute(select(User).where(User.email == email.lower()))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.hashed_password):
        raise AuthError("Invalid email or password.")
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)
