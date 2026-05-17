# app/main.py

from fastapi import FastAPI
from app.database import engine, Base
from app import models
from app.routers import books, members, authors, categories, loans, reports

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Library Lending API",
    description="A library book lending system",
    version="1.0.0"
)

app.include_router(books.router)
app.include_router(members.router)
app.include_router(authors.router)
app.include_router(categories.router)
app.include_router(loans.router)
app.include_router(reports.router)


@app.get("/api/v1/health", tags=["Health"])
def health_check():
    return {"status": "ok", "library": "open"}