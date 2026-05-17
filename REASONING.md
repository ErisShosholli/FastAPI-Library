# Reasoning — Design Choices

## Why SQLite instead of PostgreSQL

SQLite was chosen for simplicity of local development — no separate database server is required, which makes the project easy to clone and run immediately. The assignment brief explicitly states SQLite is acceptable. For a production system, PostgreSQL would be preferred for better write concurrency, stronger constraint enforcement (especially around foreign keys), and native support for more advanced query features.

---

## How I modelled the Many-to-Many relationship

Books and authors have a M:N relationship — one book can have multiple authors, and one author can write multiple books. I implemented this using an explicit association table called `book_authors` with a composite primary key of `(book_id, author_id)`.

In SQLAlchemy this is defined using `Table()` rather than a full model class, because the join table has no extra fields beyond the two foreign keys. The `relationship()` on both `Book` and `Author` uses `secondary=book_authors` to navigate the M:N link transparently in Python.

---

## How I avoided N+1 queries in the search endpoint

The search endpoint uses `joinedload()` from SQLAlchemy to eagerly load `authors` and `category` for each book in the same query rather than issuing a separate query per book.

For counting, I use a separate `COUNT(DISTINCT books.id)` query rather than calling `.count()` on the joinedloaded query — this avoids inflated counts caused by JOIN multiplying rows when a book has multiple authors.

The availability filter uses a correlated subquery (`scalar_subquery()`) that counts active loans per book inline, avoiding a separate query per book.

---

## Why DELETE on a member with active loans returns 409

A `409 Conflict` is returned rather than `200` or `204` because the delete operation conflicts with the current state of the system — the member still has books checked out that have not been returned. Deleting the member while their loans are active would leave orphaned loan records with no associated member, breaking referential integrity and making it impossible to track which member owes which book.

The correct resolution is to either return the books first, or deactivate the member (`is_active=false`) rather than deleting them entirely.

---

## How I structured the test suite

Tests are split into two files:

- `tests/test_loans.py` — covers the borrow flow, return flow, all 400/409/404 conditions, list filters, and the 409 on delete with active loans
- `tests/test_search.py` — covers filter composition, title case-insensitivity, availability filtering, year range, all sort options, pagination shape, and the empty-items behaviour beyond the last page

Each test gets a fresh database via a file-based SQLite test DB that is created before the test and deleted after. The `seed_data` fixture creates the minimum necessary data through the API itself so that auth, validation, and relationships are exercised as part of setup.

I skipped testing the report endpoints and CRUD operations for authors/categories/members directly — the core business logic is in loans and search, and those are the highest-value tests per the rubric.

---

## Scope choices

### Finished
- All CRUD endpoints for books, members, authors, categories
- Loan borrow and return with all business rule checks
- Book search with all filters, sorting, and pagination
- Reports: top borrowers and overdue loans
- Loan history per book
- API key authentication
- Seed script with realistic data
- pytest tests for loans and search

### Cut
- Alembic migrations — replaced with `Base.metadata.create_all()` for time reasons. Tables are created correctly on startup; Alembic would add versioned migration history.
- Docker — not implemented due to time constraints.

---

## External Resources Used

- FastAPI official documentation: https://fastapi.tiangolo.com
- SQLAlchemy ORM documentation: https://docs.sqlalchemy.org
- Pydantic v2 documentation: https://docs.pydantic.dev
- pytest documentation: https://docs.pytest.org
- Claude (Anthropic) — used as a learning aid to understand concepts, debug errors, and explain SQLAlchemy query patterns. All code was written and understood line by line.