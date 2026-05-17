# tests/test_search.py

from datetime import date, timedelta

HEADERS = {"X-Api-Key": "mysecretkey123"}
FUTURE_DATE = (date.today() + timedelta(days=30)).isoformat()


def test_search_returns_paginated_shape(client, seed_data):
    res = client.get("/api/v1/books/search")
    assert res.status_code == 200
    body = res.json()
    assert "items" in body
    assert "page" in body
    assert "page_size" in body
    assert "total" in body
    assert "total_pages" in body


def test_search_items_have_authors_and_category(client, seed_data):
    res = client.get("/api/v1/books/search")
    assert res.status_code == 200
    for book in res.json()["items"]:
        assert "authors" in book
        assert "category" in book
        assert isinstance(book["authors"], list)


def test_search_filter_by_title(client, seed_data):
    res = client.get("/api/v1/books/search?q=1984")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "1984"


def test_search_title_is_case_insensitive(client, seed_data):
    res = client.get("/api/v1/books/search?q=brave")
    assert res.status_code == 200
    items = res.json()["items"]
    assert any("Brave" in book["title"] for book in items)


def test_search_filter_by_category(client, seed_data):
    res = client.get(f"/api/v1/books/search?category_id={seed_data['category_id']}")
    assert res.status_code == 200
    items = res.json()["items"]
    # All 3 books are in Fiction
    assert len(items) == 3
    for book in items:
        assert book["category"]["id"] == seed_data["category_id"]


def test_search_filter_by_author(client, seed_data):
    res = client.get(f"/api/v1/books/search?author_id={seed_data['author_id']}")
    assert res.status_code == 200
    items = res.json()["items"]
    # Orwell wrote 1984 and Animal Farm
    assert len(items) == 2
    for book in items:
        author_ids = [a["id"] for a in book["authors"]]
        assert seed_data["author_id"] in author_ids


def test_search_filters_compose(client, seed_data):
    # category + author together — should only return Orwell books in Fiction
    res = client.get(
        f"/api/v1/books/search?category_id={seed_data['category_id']}&author_id={seed_data['author_id']}"
    )
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 2
    for book in items:
        assert book["category"]["id"] == seed_data["category_id"]


def test_search_available_only(client, seed_data):
    # Borrow the only copy of book2 (total_copies=1)
    client.post("/api/v1/loans", json={
        "member_id": seed_data["active_member_id"],
        "book_id": seed_data["book2_id"],
        "due_date": FUTURE_DATE
    }, headers=HEADERS)

    res = client.get("/api/v1/books/search?available_only=true")
    assert res.status_code == 200
    book_ids = [b["id"] for b in res.json()["items"]]
    # book2 is fully borrowed — should not appear
    assert seed_data["book2_id"] not in book_ids


def test_search_published_after(client, seed_data):
    res = client.get("/api/v1/books/search?published_after=1940")
    assert res.status_code == 200
    for book in res.json()["items"]:
        assert book["published_year"] >= 1940


def test_search_published_before(client, seed_data):
    res = client.get("/api/v1/books/search?published_before=1945")
    assert res.status_code == 200
    for book in res.json()["items"]:
        assert book["published_year"] <= 1945


def test_search_year_range_composes(client, seed_data):
    res = client.get("/api/v1/books/search?published_after=1932&published_before=1949")
    assert res.status_code == 200
    for book in res.json()["items"]:
        assert 1932 <= book["published_year"] <= 1949


def test_search_sort_by_title_asc(client, seed_data):
    res = client.get("/api/v1/books/search?sort_by=title&sort_order=asc")
    assert res.status_code == 200
    titles = [b["title"] for b in res.json()["items"]]
    assert titles == sorted(titles)


def test_search_sort_by_title_desc(client, seed_data):
    res = client.get("/api/v1/books/search?sort_by=title&sort_order=desc")
    assert res.status_code == 200
    titles = [b["title"] for b in res.json()["items"]]
    assert titles == sorted(titles, reverse=True)


def test_search_sort_by_published_year(client, seed_data):
    res = client.get("/api/v1/books/search?sort_by=published_year&sort_order=asc")
    assert res.status_code == 200
    years = [b["published_year"] for b in res.json()["items"]]
    assert years == sorted(years)


def test_search_sort_by_popularity(client, seed_data):
    # Borrow book1 twice so it has the most loans
    client.post("/api/v1/loans", json={
        "member_id": seed_data["active_member_id"],
        "book_id": seed_data["book1_id"],
        "due_date": FUTURE_DATE
    }, headers=HEADERS)

    res = client.get("/api/v1/books/search?sort_by=popularity&sort_order=desc")
    assert res.status_code == 200
    items = res.json()["items"]
    # book1 should appear first — it has the most loans
    assert items[0]["id"] == seed_data["book1_id"]


def test_search_invalid_sort_returns_400(client, seed_data):
    res = client.get("/api/v1/books/search?sort_by=banana")
    assert res.status_code == 400


def test_search_pagination_shape(client, seed_data):
    res = client.get("/api/v1/books/search?page=1&page_size=2")
    assert res.status_code == 200
    body = res.json()
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert len(body["items"]) == 2
    assert body["total"] == 3
    assert body["total_pages"] == 2


def test_search_pagination_page2(client, seed_data):
    res = client.get("/api/v1/books/search?page=2&page_size=2")
    assert res.status_code == 200
    body = res.json()
    assert body["page"] == 2
    assert len(body["items"]) == 1  # 3 books total, page 2 has 1


def test_search_beyond_last_page_returns_empty(client, seed_data):
    res = client.get("/api/v1/books/search?page=9999")
    assert res.status_code == 200
    body = res.json()
    assert body["items"] == []
    assert body["total"] == 3      # total stays correct