# Library Lending API

A REST API for managing a small library's book lending system. Built with FastAPI and SQLite, it allows librarians to manage books, authors, categories, and members, as well as track book loans with full borrowing and return workflows.

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| FastAPI | Web framework |
| SQLAlchemy | ORM |
| SQLite | Database |
| Pydantic | Request / response validation |
| pytest | Testing |

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/library-api.git
cd library-api
```

### 2. Create and activate a virtual environment

**Mac / Linux**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```
API_KEY=mysecretkey123
DATABASE_URL=sqlite:///./library.db
```

### 5. Start the server

```bash
uvicorn app.main:app --reload
```

- API → `http://localhost:8000`
- Interactive docs → `http://localhost:8000/docs`

### 6. Seed the database

```bash
python scripts/seed.py
```

Populates the database with 5 categories, 10 authors, 20 books, 10 members, and 35 loans (mix of active, returned, and overdue).

---

## Running Tests

```bash
python -m pytest tests/ -v
```

Tests use a separate file-based SQLite database that is created and destroyed automatically per test. No manual setup required.

---

## API Key Authentication

All `POST`, `PATCH`, and `DELETE` endpoints require an API key.

Pass it as a request header:

```
X-Api-Key: mysecretkey123
```

`GET` endpoints are open and require no authentication.

---

## Endpoints

### Health

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/health` | Health check | No |

### Books

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/books` | List all books | No |
| GET | `/api/v1/books/{id}` | Get one book | No |
| POST | `/api/v1/books` | Create a book | Yes |
| PATCH | `/api/v1/books/{id}` | Update a book | Yes |
| DELETE | `/api/v1/books/{id}` | Delete a book | Yes |
| GET | `/api/v1/books/search` | Search with filters, sort, pagination | No |
| GET | `/api/v1/books/{id}/loan-history` | Paginated loan history for a book | No |

### Members

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/members` | List all members | No |
| GET | `/api/v1/members/{id}` | Get one member | No |
| POST | `/api/v1/members` | Create a member | Yes |
| PATCH | `/api/v1/members/{id}` | Update a member | Yes |
| DELETE | `/api/v1/members/{id}` | Delete a member | Yes |

### Authors

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/authors` | List all authors | No |
| GET | `/api/v1/authors/{id}` | Get one author | No |
| POST | `/api/v1/authors` | Create an author | Yes |
| PATCH | `/api/v1/authors/{id}` | Update an author | Yes |
| DELETE | `/api/v1/authors/{id}` | Delete an author | Yes |

### Categories

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/categories` | List all categories | No |
| GET | `/api/v1/categories/{id}` | Get one category | No |
| POST | `/api/v1/categories` | Create a category | Yes |
| PATCH | `/api/v1/categories/{id}` | Update a category | Yes |
| DELETE | `/api/v1/categories/{id}` | Delete a category | Yes |

### Loans

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/loans` | Borrow a book | Yes |
| POST | `/api/v1/loans/{id}/return` | Return a book | Yes |
| GET | `/api/v1/loans` | List loans (`?status=active\|returned\|overdue`) | No |

### Reports

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/v1/reports/top-borrowers` | Top N members by total loans | No |
| GET | `/api/v1/reports/overdue-loans` | All overdue active loans | No |

> Full interactive documentation available at `/docs` when the server is running.

---

## Book Search Parameters

`GET /api/v1/books/search` supports the following query parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Partial title match (case-insensitive) |
| `category_id` | int | Filter by category |
| `author_id` | int | Filter by author |
| `available_only` | bool | Only books with copies available |
| `published_after` | int | Published year >= value |
| `published_before` | int | Published year <= value |
| `sort_by` | string | `title`, `published_year`, or `popularity` |
| `sort_order` | string | `asc` or `desc` (default `asc`) |
| `page` | int | Page number (default `1`) |
| `page_size` | int | Items per page (default `20`, max `100`) |

---

## Notes

lighthouse

This project was built as a take-home assessment for GigaAcademy Batch 5.

### Known Limitations

- SQLite is used instead of PostgreSQL. For production, PostgreSQL would be preferred for better concurrency and stronger constraint enforcement.
- No rate limiting on API key authentication.
- `DELETE /members/{id}` blocks deletion if the member has active loans but does not clean up historical returned loan records.
- Alembic migrations are not implemented. Tables are created via `Base.metadata.create_all()` on startup.