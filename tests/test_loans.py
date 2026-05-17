# tests/test_loans.py

from datetime import date, timedelta

FUTURE_DATE = (date.today() + timedelta(days=30)).isoformat()
HEADERS = {"X-Api-Key": "mysecretkey123"}


def borrow(client, member_id, book_id, due_date=None):
    # Helper to reduce repetition in tests
    return client.post("/api/v1/loans", json={
        "member_id": member_id,
        "book_id": book_id,
        "due_date": due_date or FUTURE_DATE
    }, headers=HEADERS)


# ── Borrow flow ──

def test_borrow_success(client, seed_data):
    res = borrow(client, seed_data["active_member_id"], seed_data["book1_id"])
    assert res.status_code == 201
    body = res.json()
    assert body["return_date"] is None
    assert body["member"]["id"] == seed_data["active_member_id"]
    assert body["book"]["id"] == seed_data["book1_id"]


def test_borrow_inactive_member_returns_400(client, seed_data):
    res = borrow(client, seed_data["inactive_member_id"], seed_data["book1_id"])
    assert res.status_code == 400


def test_borrow_nonexistent_member_returns_404(client, seed_data):
    res = borrow(client, 99999, seed_data["book1_id"])
    assert res.status_code == 404


def test_borrow_nonexistent_book_returns_404(client, seed_data):
    res = borrow(client, seed_data["active_member_id"], 99999)
    assert res.status_code == 404


def test_borrow_no_copies_available_returns_409(client, seed_data):
    # book2 has total_copies=1 — borrow it once, second attempt should 409
    first = borrow(client, seed_data["active_member_id"], seed_data["book2_id"])
    assert first.status_code == 201

    second = borrow(client, seed_data["active_member_id"], seed_data["book2_id"])
    assert second.status_code == 409


def test_borrow_respects_total_copies(client, seed_data):
    # book1 has total_copies=2 — both borrows should succeed
    first = borrow(client, seed_data["active_member_id"], seed_data["book1_id"])
    assert first.status_code == 201

    second = borrow(client, seed_data["active_member_id"], seed_data["book1_id"])
    assert second.status_code == 201

    # Third borrow should fail — no copies left
    third = borrow(client, seed_data["active_member_id"], seed_data["book1_id"])
    assert third.status_code == 409


def test_borrow_past_due_date_returns_422(client, seed_data):
    # Pydantic validator rejects past due dates
    res = client.post("/api/v1/loans", json={
        "member_id": seed_data["active_member_id"],
        "book_id": seed_data["book1_id"],
        "due_date": "2020-01-01"
    }, headers=HEADERS)
    assert res.status_code == 422


# ── Return flow ──

def test_return_success(client, seed_data):
    loan = borrow(client, seed_data["active_member_id"], seed_data["book1_id"])
    loan_id = loan.json()["id"]

    res = client.post(f"/api/v1/loans/{loan_id}/return", headers=HEADERS)
    assert res.status_code == 200
    assert res.json()["return_date"] is not None


def test_return_sets_return_date_to_today(client, seed_data):
    loan = borrow(client, seed_data["active_member_id"], seed_data["book1_id"])
    loan_id = loan.json()["id"]

    client.post(f"/api/v1/loans/{loan_id}/return", headers=HEADERS)
    res = client.post(f"/api/v1/loans/{loan_id}/return", headers=HEADERS)

    # Second return attempt should be 409
    assert res.status_code == 409


def test_return_already_returned_returns_409(client, seed_data):
    loan = borrow(client, seed_data["active_member_id"], seed_data["book1_id"])
    loan_id = loan.json()["id"]

    client.post(f"/api/v1/loans/{loan_id}/return", headers=HEADERS)
    res = client.post(f"/api/v1/loans/{loan_id}/return", headers=HEADERS)
    assert res.status_code == 409


def test_return_nonexistent_loan_returns_404(client, seed_data):
    res = client.post("/api/v1/loans/99999/return", headers=HEADERS)
    assert res.status_code == 404


def test_return_frees_up_copy(client, seed_data):
    # book2 has 1 copy — borrow, return, then borrow again should work
    loan = borrow(client, seed_data["active_member_id"], seed_data["book2_id"])
    assert loan.status_code == 201
    loan_id = loan.json()["id"]

    client.post(f"/api/v1/loans/{loan_id}/return", headers=HEADERS)

    second = borrow(client, seed_data["active_member_id"], seed_data["book2_id"])
    assert second.status_code == 201


# ── List loans ──

def test_list_loans_returns_paginated_shape(client, seed_data):
    borrow(client, seed_data["active_member_id"], seed_data["book1_id"])

    res = client.get("/api/v1/loans")
    assert res.status_code == 200
    body = res.json()
    assert "items" in body
    assert "page" in body
    assert "page_size" in body
    assert "total" in body
    assert "total_pages" in body


def test_list_loans_filter_by_member(client, seed_data):
    borrow(client, seed_data["active_member_id"], seed_data["book1_id"])

    res = client.get(f"/api/v1/loans?member_id={seed_data['active_member_id']}")
    assert res.status_code == 200
    for loan in res.json()["items"]:
        assert loan["member"]["id"] == seed_data["active_member_id"]


def test_list_loans_filter_by_status_active(client, seed_data):
    borrow(client, seed_data["active_member_id"], seed_data["book1_id"])

    res = client.get("/api/v1/loans?status=active")
    assert res.status_code == 200
    for loan in res.json()["items"]:
        assert loan["return_date"] is None


def test_list_loans_filter_by_status_returned(client, seed_data):
    loan = borrow(client, seed_data["active_member_id"], seed_data["book1_id"])
    client.post(f"/api/v1/loans/{loan.json()['id']}/return", headers=HEADERS)

    res = client.get("/api/v1/loans?status=returned")
    assert res.status_code == 200
    for loan in res.json()["items"]:
        assert loan["return_date"] is not None


def test_list_loans_invalid_status_returns_400(client, seed_data):
    res = client.get("/api/v1/loans?status=banana")
    assert res.status_code == 400


def test_delete_member_with_active_loan_returns_409(client, seed_data):
    borrow(client, seed_data["active_member_id"], seed_data["book1_id"])

    res = client.delete(
        f"/api/v1/members/{seed_data['active_member_id']}",
        headers=HEADERS
    )
    assert res.status_code == 409