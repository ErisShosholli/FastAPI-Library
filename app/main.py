from fastapi import FastAPI

# Import the engine (our DB connection) and Base (parent of all models)
from app.database import engine, Base

# Import models so SQLAlchemy knows about them before create_all runs
from app import models

# Create all tables in the database
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Library Lending API",
    description="A library book lending system",
    version="1.0.0"
)

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "library": "open"}