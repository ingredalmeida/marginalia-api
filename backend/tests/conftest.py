"""Infraestrutura compartilhada: app FastAPI + SQLite em memória + overrides."""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.core.rate_limit import limiter
from app.core.security import hash_password
from app.main import app
from app.models import Author, Book, User
from app.models.base import Base


@event.listens_for(Engine, "connect")
def _sqlite_enable_foreign_keys(dbapi_conn, _connection_record):
    if "sqlite" in type(dbapi_conn).__module__:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


@pytest.fixture(autouse=True)
def _reset_rate_limits() -> None:
    """Evita 429 em sequências de register/login (slowapi por IP)."""
    limiter.reset()


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_maker(test_engine):
    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


@pytest_asyncio.fixture
async def client(test_engine, session_maker) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def register_patron(
    client: AsyncClient,
    *,
    email: str = "patron@example.com",
    password: str = "SenhaSegura1",
    name: str = "Patrono Teste",
) -> dict:
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "name": name},
    )
    assert r.status_code == 201, r.text
    return r.json()


async def login(client: AsyncClient, email: str, password: str) -> str:
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def bearer_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def create_admin_user(session_maker, *, email: str = "admin@example.com") -> User:
    async with session_maker() as session:
        user = User(
            name="Admin Teste",
            email=email,
            hashed_password=hash_password("AdminSenha1"),
            is_admin=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def seed_author_and_books(session_maker, n_books: int = 1) -> tuple[int, list[int]]:
    async with session_maker() as session:
        author = Author(name="Autor Teste", bio=None)
        session.add(author)
        await session.flush()
        book_ids: list[int] = []
        for i in range(n_books):
            b = Book(
                title=f"Livro {i}",
                author_id=author.id,
                description=None,
                publisher=None,
                isbn=None,
                publication_year=2020,
            )
            session.add(b)
            await session.flush()
            book_ids.append(b.id)
        await session.commit()
        return author.id, book_ids
