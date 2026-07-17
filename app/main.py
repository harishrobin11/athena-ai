"""
Athena AI - Main Application Entry Point
Description: Initializes the FastAPI application state and mounts 
             the unified routing engine.
"""

from dotenv import load_dotenv
load_dotenv(override=True)

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.api.v1.vault import router as vault_router
from app.api.v1.agent import router as agent_router
from app.api.organizations import router as org_router
from app.api.workspaces import router as workspace_router

# 🦉 Instantiate the core FastAPI engine context exactly ONCE
app = FastAPI(
    title="Athena AI Core Engine",
    description="Sprint 8 Production API & Sprint 21 Architecture Unified API Gateway — Multi-Tenant Isolation",
    version="21.0.0",
    contact={
        "name": "Athena AI Team",
        "url": "http://athena-ai.local",
    },
    license_info={
        "name": "Proprietary",
    },
    openapi_tags=[
        {"name": "Auth", "description": "Authentication and user management"},
        {"name": "Agent", "description": "Conversational AI and chat endpoints"},
        {"name": "Vault", "description": "Memory and RAG document storage"},
        {"name": "Tenants", "description": "Multi-tenant workspace operations"}
    ]
)

# OpenTelemetry Instrumentation (Sprint 25)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
FastAPIInstrumentor.instrument_app(app)

# Prometheus Instrumentation (Sprints 26-30)
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)

# Enable CORS so your Streamlit UI can communicate cleanly across localhost ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        field = ".".join([str(loc) for loc in err.get("loc", [])])
        errors.append({"field": field, "message": err.get("msg")})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": {"code": "VALIDATION_ERROR", "details": errors}},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."}},
    )

@app.get("/", tags=["Health"])
async def root_health_check():
    return {"status": "online", "system": "Athena-AI Core Gateway"}

# 🔄 ROUTER REGISTRATIONS DIRECTLY TO APP CONTEXT
# 1. Mount the Conversational Agent Stream Gateway (/api/v1/agent/chat)
app.include_router(agent_router, prefix="/api/v1", tags=["Agent"])

# 2. Mount the Module 10 Memory Vault Database Router (/api/v1/vault)
app.include_router(vault_router, prefix="/api/v1", tags=["Vault"])

# 3. Mount the unified root router (handles /login, /register, etc.)
app.include_router(api_router, tags=["Auth"])

# 4. Mount the Multi-Tenant routers
app.include_router(org_router, tags=["Tenants"])
app.include_router(workspace_router, tags=["Tenants"])

if __name__ == "__main__":
    import uvicorn
    # 🛠️ FIXED: Uses simple string module configuration matching the root terminal run rules
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)