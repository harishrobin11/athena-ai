from fastapi import FastAPI

app = FastAPI(
    title="Athena AI",
    description="Enterprise Intelligence Platform",
    version="0.1.0"
)


@app.get("/")
def root():
    return {
        "application": "Athena AI",
        "status": "Running",
        "version": "0.1.0"
    }