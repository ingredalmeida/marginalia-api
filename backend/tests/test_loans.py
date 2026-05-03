from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.models import Loan
from tests.conftest import (
    bearer_headers,
    create_admin_user,
    login,
    register_patron,
    seed_author_and_books,
)


@pytest.mark.asyncio
async def test_create_loan_happy_path(client: AsyncClient, session_maker):
    _, book_ids = await seed_author_and_books(session_maker, n_books=1)
    reg = await register_patron(client, email="borrower@example.com")
    uid = reg["id"]
    token = await login(client, "borrower@example.com", "SenhaSegura1")
    r = await client.post(
        "/api/v1/loans",
        headers=bearer_headers(token),
        json={"user_id": uid, "book_id": book_ids[0]},
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["book_id"] == book_ids[0]
    assert data["user_id"] == uid
    borrowed = datetime.fromisoformat(data["borrowed_at"].replace("Z", "+00:00"))
    due = datetime.fromisoformat(data["due_at"].replace("Z", "+00:00"))
    assert (due.date() - borrowed.date()).days == 14


@pytest.mark.asyncio
async def test_second_loan_same_book_conflict(client: AsyncClient, session_maker):
    _, book_ids = await seed_author_and_books(session_maker, n_books=1)
    await create_admin_user(session_maker, email="admin2@example.com")
    admin_tok = await login(client, "admin2@example.com", "AdminSenha1")
    a_reg = await register_patron(client, email="a@example.com")
    b_reg = await register_patron(client, email="b@example.com")
    a_tok = await login(client, "a@example.com", "SenhaSegura1")
    b_tok = await login(client, "b@example.com", "SenhaSegura1")

    r1 = await client.post(
        "/api/v1/loans",
        headers=bearer_headers(a_tok),
        json={"user_id": a_reg["id"], "book_id": book_ids[0]},
    )
    assert r1.status_code == 201
    r2 = await client.post(
        "/api/v1/loans",
        headers=bearer_headers(admin_tok),
        json={"user_id": b_reg["id"], "book_id": book_ids[0]},
    )
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_max_three_active_loans(client: AsyncClient, session_maker):
    _, book_ids = await seed_author_and_books(session_maker, n_books=4)
    reg = await register_patron(client, email="heavy@example.com")
    uid = reg["id"]
    token = await login(client, "heavy@example.com", "SenhaSegura1")
    for i in range(3):
        r = await client.post(
            "/api/v1/loans",
            headers=bearer_headers(token),
            json={"user_id": uid, "book_id": book_ids[i]},
        )
        assert r.status_code == 201, r.text
    r4 = await client.post(
        "/api/v1/loans",
        headers=bearer_headers(token),
        json={"user_id": uid, "book_id": book_ids[3]},
    )
    assert r4.status_code == 409


@pytest.mark.asyncio
async def test_return_on_due_date_zero_fine(client: AsyncClient, session_maker):
    _, book_ids = await seed_author_and_books(session_maker, n_books=1)
    reg = await register_patron(client, email="ret@example.com")
    token = await login(client, "ret@example.com", "SenhaSegura1")
    r_loan = await client.post(
        "/api/v1/loans",
        headers=bearer_headers(token),
        json={"user_id": reg["id"], "book_id": book_ids[0]},
    )
    loan_id = r_loan.json()["id"]
    due_raw = r_loan.json()["due_at"]
    due = datetime.fromisoformat(due_raw.replace("Z", "+00:00"))

    with patch("app.services.loan_service.datetime") as md:
        md.now = lambda tz=None: due
        r_ret = await client.post(
            f"/api/v1/loans/{loan_id}/return",
            headers=bearer_headers(token),
        )
    assert r_ret.status_code == 200, r_ret.text
    assert Decimal(r_ret.json()["fine_amount"]) == Decimal("0")


@pytest.mark.asyncio
async def test_return_overdue_fine_per_day(client: AsyncClient, session_maker):
    _, book_ids = await seed_author_and_books(session_maker, n_books=1)
    reg = await register_patron(client, email="late@example.com")
    token = await login(client, "late@example.com", "SenhaSegura1")
    r_loan = await client.post(
        "/api/v1/loans",
        headers=bearer_headers(token),
        json={"user_id": reg["id"], "book_id": book_ids[0]},
    )
    loan_id = r_loan.json()["id"]
    due_raw = r_loan.json()["due_at"]
    due = datetime.fromisoformat(due_raw.replace("Z", "+00:00"))
    return_moment = due + timedelta(days=3)

    with patch("app.services.loan_service.datetime") as md:
        md.now = lambda tz=None: return_moment
        r_ret = await client.post(
            f"/api/v1/loans/{loan_id}/return",
            headers=bearer_headers(token),
        )
    assert r_ret.status_code == 200
    assert Decimal(r_ret.json()["fine_amount"]) == Decimal("6.00")


@pytest.mark.asyncio
async def test_renew_once_extends_due_date(client: AsyncClient, session_maker):
    _, book_ids = await seed_author_and_books(session_maker, n_books=1)
    reg = await register_patron(client, email="ren@example.com")
    token = await login(client, "ren@example.com", "SenhaSegura1")
    r_loan = await client.post(
        "/api/v1/loans",
        headers=bearer_headers(token),
        json={"user_id": reg["id"], "book_id": book_ids[0]},
    )
    loan_id = r_loan.json()["id"]
    old_due = datetime.fromisoformat(r_loan.json()["due_at"].replace("Z", "+00:00"))
    r_new = await client.post(
        f"/api/v1/loans/{loan_id}/renew",
        headers=bearer_headers(token),
    )
    assert r_new.status_code == 200, r_new.text
    new_due = datetime.fromisoformat(r_new.json()["due_at"].replace("Z", "+00:00"))
    assert (new_due - old_due).days == 4
    assert r_new.json()["renewal_count"] == 1
    r_twice = await client.post(
        f"/api/v1/loans/{loan_id}/renew",
        headers=bearer_headers(token),
    )
    assert r_twice.status_code == 409


@pytest.mark.asyncio
async def test_renew_when_overdue_bad_request(client: AsyncClient, session_maker):
    _, book_ids = await seed_author_and_books(session_maker, n_books=1)
    reg = await register_patron(client, email="ov@example.com")
    token = await login(client, "ov@example.com", "SenhaSegura1")
    r_loan = await client.post(
        "/api/v1/loans",
        headers=bearer_headers(token),
        json={"user_id": reg["id"], "book_id": book_ids[0]},
    )
    loan_id = r_loan.json()["id"]
    utc = timezone.utc
    past_due = datetime.now(utc) - timedelta(days=1)
    async with session_maker() as session:
        loan = await session.get(Loan, loan_id)
        loan.due_at = past_due
        await session.commit()

    r_new = await client.post(
        f"/api/v1/loans/{loan_id}/renew",
        headers=bearer_headers(token),
    )
    assert r_new.status_code == 400


@pytest.mark.asyncio
async def test_renew_after_seven_day_window_bad_request(client: AsyncClient, session_maker):
    _, book_ids = await seed_author_and_books(session_maker, n_books=1)
    reg = await register_patron(client, email="old@example.com")
    token = await login(client, "old@example.com", "SenhaSegura1")
    r_loan = await client.post(
        "/api/v1/loans",
        headers=bearer_headers(token),
        json={"user_id": reg["id"], "book_id": book_ids[0]},
    )
    loan_id = r_loan.json()["id"]
    utc = timezone.utc
    borrowed_old = datetime.now(utc) - timedelta(days=10)
    due_future = datetime.now(utc) + timedelta(days=10)
    async with session_maker() as session:
        loan = await session.get(Loan, loan_id)
        loan.borrowed_at = borrowed_old
        loan.due_at = due_future
        loan.renewal_count = 0
        await session.commit()

    r_new = await client.post(
        f"/api/v1/loans/{loan_id}/renew",
        headers=bearer_headers(token),
    )
    assert r_new.status_code == 400
