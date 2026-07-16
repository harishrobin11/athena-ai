"""
Athena AI - Main Application Entry Point
Description: Initializes the FastAPI application state and mounts 
             the unified routing engine.
"""

from dotenv import load_dotenv
load_dotenv(override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.api.v1.vault import router as vault_router
from app.api.v1.agent import router as agent_router
from app.api.organizations import router as org_router
from app.api.workspaces import router as workspace_router

# 🦉 Instantiate the core FastAPI engine context exactly ONCE
app = FastAPI(
    title="Athena AI Core Engine",
    description="Sprint 21 Architecture Unified API Gateway — Multi-Tenant Isolation",
    version="21.0.0"
)

# OpenTelemetry Instrumentation (Sprint 25)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
FastAPIInstrumentor.instrument_app(app)

# Enable CORS so your Streamlit UI can communicate cleanly across localhost ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root_health_check():
    return {"status": "online", "system": "Athena-AI Core Gateway"}

# 🔄 ROUTER REGISTRATIONS DIRECTLY TO APP CONTEXT
# 1. Mount the Conversational Agent Stream Gateway (/api/v1/agent/chat)
app.include_router(agent_router, prefix="/api/v1")

# 2. Mount the Module 10 Memory Vault Database Router (/api/v1/vault)
app.include_router(vault_router, prefix="/api/v1")

# 3. Mount the unified root router (handles /login, /register, etc.)
app.include_router(api_router)

# 4. Mount the Multi-Tenant routers
app.include_router(org_router)
app.include_router(workspace_router)

if __name__ == "__main__":
    import uvicorn
    # 🛠️ FIXED: Uses simple string module configuration matching the root terminal run rules
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)