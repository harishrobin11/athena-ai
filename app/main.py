"""
Athena AI - Main Application Entry Point
Description: Initializes the FastAPI application state and mounts 
             the unified routing engine.
"""

from dotenv import load_dotenv
load_dotenv(override=True)

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.api.routes import router as api_router
from app.api.v1.vault import router as vault_router
from app.api.v1.agent import router as agent_router
from app.api.v1.metrics import router as metrics_router
from app.api.admin import router as admin_router
from app.api.knowledge import router as knowledge_router
from app.api.marketplace import router as marketplace_router
from app.api.organizations import router as org_router
from app.api.workspaces import router as workspace_router
from app.api.billing import router as billing_router
from app.api.notifications import router as notifications_router
from app.api.cache import router as cache_router
from app.api.security import router as security_router
try:
    from fastapi_limiter import FastAPILimiter
except Exception:
    FastAPILimiter = None

from app.db.redis import redis_manager
from contextlib import asynccontextmanager
from app.core.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.memory.database import init_db
    try:
        init_db()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
    try:
        await redis_manager.connect()
        client = redis_manager.get_client()
        if client and FastAPILimiter is not None:
            await FastAPILimiter.init(client)
            logger.info("FastAPILimiter initialized")
    except Exception as e:
        logger.warning(f"Redis / FastAPILimiter startup bypassed: {e}")
    yield
    try:
        await redis_manager.close()
    except Exception:
        pass


# Instantiate the core FastAPI engine context exactly ONCE
app = FastAPI(
    title="Athena AI Core Engine",
    description="Sprint 8 Production API & Sprint 21 Architecture Unified API Gateway — Multi-Tenant Isolation",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
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

# OpenTelemetry & Prometheus Instrumentation
try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    FastAPIInstrumentor.instrument_app(app)
except Exception as e:
    logger.warning(f"OpenTelemetry instrumentation bypassed: {e}")

try:
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app)
except Exception as e:
    logger.warning(f"Prometheus instrumentation bypassed: {e}")


# GZip compression for all responses > 1KB (Sprint 54)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Enable CORS so your React UI can communicate cleanly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Performance Timing Middleware (Sprint 54) ─────────────────────────────────
@app.middleware("http")
async def add_performance_headers(request: Request, call_next):
    import time
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
    response.headers["X-Server"] = "Athena-AI/1.0"
    return response

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
    logger.error("Unhandled API exception", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."}},
    )

from fastapi.responses import RedirectResponse

@app.get("/", tags=["Health"])
async def root_health_check():
    return {"status": "online", "system": "Athena-AI Core Gateway"}

@app.get("/docs", include_in_schema=False)
async def redirect_docs():
    return RedirectResponse(url="/api/docs")

# 1. Mount the Conversational Agent Stream Gateway (/api/v1/agent/chat)
app.include_router(agent_router, prefix="/api/v1", tags=["Agent"])

# 2. Mount the Module 10 Memory Vault Database Router (/api/v1/vault)
app.include_router(vault_router, prefix="/api/v1", tags=["Vault"])

# Mount Live Metrics Router
app.include_router(metrics_router, prefix="/api/v1", tags=["Metrics"])

app.include_router(api_router, prefix="/api", tags=["core"])
app.include_router(admin_router, prefix="/api", tags=["admin"])
app.include_router(knowledge_router, prefix="/api/knowledge", tags=["knowledge"])
app.include_router(marketplace_router, prefix="/api/marketplace", tags=["marketplace"])

# 3. Mount the unified root router (handles /login, /register, etc.)
app.include_router(api_router, tags=["Auth"])

# 4. Mount the Multi-Tenant routers
app.include_router(org_router, tags=["Tenants"])
app.include_router(workspace_router, tags=["Tenants"])
app.include_router(billing_router)

# 5. Mount the Admin router
app.include_router(admin_router)

# 6. Mount Notification System (Sprint 51)
app.include_router(notifications_router)

# 7. Mount Cache Management (Sprint 54)
app.include_router(cache_router)

# 8. Mount Enterprise Security (Sprint 55)
app.include_router(security_router)

if __name__ == "__main__":
    import uvicorn
    # 🛠️ FIXED: Uses simple string module configuration matching the root terminal run rules
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)