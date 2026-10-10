from fastapi import FastAPI
from app.core.errors import register_exception_handlers

app = FastAPI(title="Geospatial File Measurement API")

register_exception_handlers(app)

@app.get("/health")
def health():
    return {"status": "ok"}
