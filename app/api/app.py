from fastapi import FastAPI
from .routes import router

app = FastAPI(
    title="Athena AI API",
    description="Enterprise AI Assistant API",
    version="1.0.0",
)

app.include_router(router)