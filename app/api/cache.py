"""
Athena AI - Cache Management API (Sprint 54 - Performance Optimization)
Endpoints to inspect and manage the Redis cache.
"""

from fastapi import APIRouter
from app.services.cache import metrics_cache, prompt_cache, search_cache, user_cache

router = APIRouter(prefix="/api/cache", tags=["Cache"])


@router.get("/stats")
async def cache_stats():
    """Return Redis cache memory usage and stats."""
    return await metrics_cache.get_stats()


@router.delete("/flush/{namespace}")
async def flush_cache_namespace(namespace: str):
    """
    Flush a specific cache namespace.
    namespace: metrics | prompts | search | users | all
    """
    deleted = 0
    if namespace == "metrics" or namespace == "all":
        deleted += await metrics_cache.delete_pattern("*")
    if namespace == "prompts" or namespace == "all":
        deleted += await prompt_cache.delete_pattern("*")
    if namespace == "search" or namespace == "all":
        deleted += await search_cache.delete_pattern("*")
    if namespace == "users" or namespace == "all":
        deleted += await user_cache.delete_pattern("*")
    return {"success": True, "namespace": namespace, "keys_deleted": deleted}


@router.get("/health")
async def cache_health():
    """Quick Redis connectivity check."""
    from app.db.redis import redis_manager
    client = redis_manager.get_client()
    if not client:
        return {"status": "unavailable"}
    try:
        pong = await client.ping()
        return {"status": "healthy", "ping": pong}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
