from fastapi import FastAPI
from .routes import router
from app.memory.database import init_db

app = FastAPI(
    title="Athena AI API",
    description="Enterprise AI Assistant API",
    version="1.0.0",
)

@app.on_event("startup")
def startup():
    init_db()

app.include_router(router)