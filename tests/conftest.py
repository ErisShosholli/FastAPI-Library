# tests/conftest.py

import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

TEST_DB_PATH = "./test_library.db"
SQLITE_TEST_URL = f"sqlite:///{TEST_DB_PATH}"

engine = create_engine(
    SQLITE_TEST_URL,
    connect_args={"check_same_thread": False}
)

@event.listens_for(engine, "connect")
def enable_fk(dbapi_conn, record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as c:
        yield c

    Base.metadata.drop_all(bind=engine)
    engine.dispose()                    # ← ADD THIS LINE
    app.dependency_overrides.clear()

    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest.fixture()
def seed_data(client):
    headers = {"X-Api-Key": "mysecretkey123"}

    cat = client.post("/api/v1/categories", json={"name": "Fiction"}, headers=headers)
    category_id = cat.json()["id"]

    a1 = client.post("/api/v1/authors", json={"full_name": "George Orwell", "country": "UK"}, headers=headers)
    a2 = client.post("/api/v1/authors", json={"full_name": "Aldous Huxley", "country": "UK"}, headers=headers)
    author_id = a1.json()["id"]

    book1 = client.post("/api/v1/books", json={
        "title": "1984",
        "isbn": "978-0451524935",
        "category_id": category_id,
        "total_copies": 2,
        "published_year": 1949,
        "author_ids": [a1.json()["id"]]
    }, headers=headers)

    book2 = client.post("/api/v1/books", json={
        "title": "Brave New World",
        "isbn": "978-0060850524",
        "category_id": category_id,
        "total_copies": 1,
        "published_year": 1932,
        "author_ids": [a2.json()["id"]]
    }, headers=headers)

    book3 = client.post("/api/v1/books", json={
        "title": "Animal Farm",
        "isbn": "978-0451526342",
        "category_id": category_id,
        "total_copies": 1,
        "published_year": 1945,
        "author_ids": [a1.json()["id"]]
    }, headers=headers)

    active_member = client.post("/api/v1/members", json={
        "full_name": "Alice Johnson",
        "email": "alice@example.com",
        "is_active": True
    }, headers=headers)

    inactive_member = client.post("/api/v1/members", json={
        "full_name": "Jack Taylor",
        "email": "jack@example.com",
        "is_active": False
    }, headers=headers)

    return {
        "category_id": category_id,
        "author_id": author_id,
        "book1_id": book1.json()["id"],
        "book2_id": book2.json()["id"],
        "book3_id": book3.json()["id"],
        "active_member_id": active_member.json()["id"],
        "inactive_member_id": inactive_member.json()["id"],
        "headers": headers
    }