import pytest
from httpx import AsyncClient

from tests.conftest import bearer_headers, login, register_patron, seed_author_and_books


@pytest.mark.asyncio
async def test_cannot_reserve_available_copy(client: AsyncClient, session_maker):
    _, book_ids = await seed_author_and_books(session_maker, n_books=1)
    reg = await register_patron(client, email="solo@example.com")
    token = await login(client, "solo@example.com", "SenhaSegura1")
    r = await client.post(
        "/api/v1/reservations",
        headers=bearer_headers(token),
        json={"user_id": reg["id"], "book_id": book_ids[0]},
    )
    assert r.status_code == 409
    assert "emprestado" in r.json()["detail"].lower() or "fila" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_can_reserve_when_copy_is_on_loan(client: AsyncClient, session_maker):
    _, book_ids = await seed_author_and_books(session_maker, n_books=1)
    h_reg = await register_patron(client, email="holder@example.com")
    w_reg = await register_patron(client, email="waiter@example.com")
    h_tok = await login(client, "holder@example.com", "SenhaSegura1")
    w_tok = await login(client, "waiter@example.com", "SenhaSegura1")

    r_loan = await client.post(
        "/api/v1/loans",
        headers=bearer_headers(h_tok),
        json={"user_id": h_reg["id"], "book_id": book_ids[0]},
    )
    assert r_loan.status_code == 201

    r_res = await client.post(
        "/api/v1/reservations",
        headers=bearer_headers(w_tok),
        json={"user_id": w_reg["id"], "book_id": book_ids[0]},
    )
    assert r_res.status_code == 201, r_res.text
    assert r_res.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_only_head_of_queue_can_borrow_after_return_and_hold(client: AsyncClient, session_maker):
    """Com o exemplar devolvido, o líder da fila pode ficar em *hold* (cheio na estante).
    Outro patrono não pode furar: o erro vem da regra da fila, não de «já emprestado»."""
    _, book_ids = await seed_author_and_books(session_maker, n_books=4)
    p1 = await register_patron(client, email="head@example.com")
    p2 = await register_patron(client, email="full@example.com")
    p3 = await register_patron(client, email="skip@example.com")
    t1 = await login(client, "head@example.com", "SenhaSegura1")
    t2 = await login(client, "full@example.com", "SenhaSegura1")
    t3 = await login(client, "skip@example.com", "SenhaSegura1")
    held_copy = book_ids[3]
    other = book_ids[:3]

    for bid in other:
        r = await client.post(
            "/api/v1/loans",
            headers=bearer_headers(t2),
            json={"user_id": p2["id"], "book_id": bid},
        )
        assert r.status_code == 201, r.text

    r_loan = await client.post(
        "/api/v1/loans",
        headers=bearer_headers(t1),
        json={"user_id": p1["id"], "book_id": held_copy},
    )
    assert r_loan.status_code == 201

    r_res = await client.post(
        "/api/v1/reservations",
        headers=bearer_headers(t2),
        json={"user_id": p2["id"], "book_id": held_copy},
    )
    assert r_res.status_code == 201

    r_ret = await client.post(
        f"/api/v1/loans/{r_loan.json()['id']}/return",
        headers=bearer_headers(t1),
    )
    assert r_ret.status_code == 200

    r_skip = await client.post(
        "/api/v1/loans",
        headers=bearer_headers(t3),
        json={"user_id": p3["id"], "book_id": held_copy},
    )
    assert r_skip.status_code == 409
    detail = r_skip.json()["detail"].lower()
    assert "fila" in detail or "espera" in detail
