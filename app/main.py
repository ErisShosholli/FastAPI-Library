from fastapi import FastAPI

app = FastAPI(
    title="Library Lending API",        
    description="A library book lending system",
    version="1.0.0"
)

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "library": "open"}
