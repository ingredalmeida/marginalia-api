import pytest
from httpx import AsyncClient

from tests.conftest import bearer_headers, create_admin_user, login, register_patron


@pytest.mark.asyncio
async def test_patron_cannot_create_author(client: AsyncClient, session_maker):
    await register_patron(client, email="pat@example.com")
    token = await login(client, "pat@example.com", "SenhaSegura1")
    r = await client.post(
        "/api/v1/authors",
        headers=bearer_headers(token),
        json={"name": "Clarice Lispector", "bio": "—"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_create_author(client: AsyncClient, session_maker):
    await create_admin_user(session_maker, email="adm@example.com")
    token = await login(client, "adm@example.com", "AdminSenha1")
    r = await client.post(
        "/api/v1/authors",
        headers=bearer_headers(token),
        json={"name": "Machado de Assis", "bio": "—"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Machado de Assis"
    assert "id" in data
