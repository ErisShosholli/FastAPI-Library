from fastapi import FastAPI
from app.database import engine, Base
from app import models

# Import all routers
from app.routers import books, members, authors, categories

# Create all database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Library Lending API",
    description="A library book lending system",
    version="1.0.0"
)

# Register each router with the app
# This is like: app.use('/api/v1/books', booksRouter) in Express
app.include_router(books.router)
app.include_router(members.router)
app.include_router(authors.router)
app.include_router(categories.router)


# Health check endpoint
@app.get("/api/v1/health", tags=["Health"])
def health_check():
    return {"status": "ok", "library": "open"}