import pytest
from httpx import AsyncClient

from tests.conftest import bearer_headers, login, register_patron


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    await register_patron(client, email="nova@example.com", password="SenhaSegura1")
    token = await login(client, "nova@example.com", "SenhaSegura1")
    assert isinstance(token, str) and len(token) > 20


@pytest.mark.asyncio
async def test_register_duplicate_email_conflict(client: AsyncClient):
    await register_patron(client, email="dup@example.com")
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dup@example.com",
            "password": "OutraSenha2",
            "name": "Outro",
        },
    )
    assert r.status_code == 409
    assert "email" in r.json()["detail"].lower() or "registered" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_wrong_password_unauthorized(client: AsyncClient):
    await register_patron(client, email="u@example.com", password="SenhaSegura1")
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": "u@example.com", "password": "Erradaaaa1"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_without_token(client: AsyncClient):
    r = await client.get("/api/v1/books")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_with_valid_token(client: AsyncClient):
    await register_patron(client, email="tok@example.com")
    token = await login(client, "tok@example.com", "SenhaSegura1")
    r = await client.get("/api/v1/books", headers=bearer_headers(token))
    assert r.status_code == 200
