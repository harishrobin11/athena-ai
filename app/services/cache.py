"""
Athena AI - Redis Cache Service (Sprint 54 - Performance Optimization)
Replaces in-memory TTLCache with Redis-backed distributed caching.
"""

import json
import hashlib
import functools
from typing import Any, Optional, Callable
from datetime import datetime

from app.db.redis import redis_manager
from app.core.logger import logger


class RedisCache:
    """
    Redis-backed distributed cache with TTL support.
    Falls back gracefully if Redis is unavailable.
    """

    def __init__(self, prefix: str = "athena:cache", default_ttl: int = 300):
        self.prefix = prefix
        self.default_ttl = default_ttl

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> Optional[Any]:
        client = redis_manager.get_client()
        if not client:
            return None
        try:
            raw = await client.get(self._key(key))
            if raw:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(raw)
            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.warning(f"Cache GET error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        client = redis_manager.get_client()
        if not client:
            return False
        try:
            await client.setex(
                self._key(key),
                ttl or self.default_ttl,
                json.dumps(value, default=str)
            )
            logger.debug(f"Cache SET: {key} (ttl={ttl or self.default_ttl}s)")
            return True
        except Exception as e:
            logger.warning(f"Cache SET error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        client = redis_manager.get_client()
        if not client:
            return False
        try:
            await client.delete(self._key(key))
            return True
        except Exception as e:
            logger.warning(f"Cache DELETE error: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern. Returns count deleted."""
        client = redis_manager.get_client()
        if not client:
            return 0
        try:
            keys = await client.keys(self._key(pattern))
            if keys:
                return await client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache pattern DELETE error: {e}")
            return 0

    async def get_stats(self) -> dict:
        """Return cache memory usage and key count."""
        client = redis_manager.get_client()
        if not client:
            return {"status": "unavailable"}
        try:
            info = await client.info("memory")
            keys = await client.dbsize()
            return {
                "status": "connected",
                "total_keys": keys,
                "used_memory_human": info.get("used_memory_human", "N/A"),
                "used_memory_peak_human": info.get("used_memory_peak_human", "N/A"),
                "maxmemory_human": info.get("maxmemory_human", "N/A"),
            }
        except Exception as e:
            return {"status": "error", "detail": str(e)}


def make_cache_key(*args, **kwargs) -> str:
    """Generate a stable hash key from arguments."""
    raw = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    return hashlib.md5(raw.encode()).hexdigest()


def cached(ttl: int = 300, prefix: str = "fn"):
    """
    Async function decorator for Redis response caching.
    Usage:
        @cached(ttl=60, prefix="metrics")
        async def get_metrics(...):
            ...
    """
    cache = RedisCache(prefix=f"athena:fn:{prefix}", default_ttl=ttl)

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Skip 'self' or 'cls' in key generation
            key_args = args[1:] if args and hasattr(args[0], '__class__') else args
            cache_key = make_cache_key(*key_args, **kwargs)

            cached_val = await cache.get(cache_key)
            if cached_val is not None:
                return cached_val

            result = await func(*args, **kwargs)

            # Only cache serializable results
            try:
                await cache.set(cache_key, result, ttl=ttl)
            except Exception:
                pass

            return result
        return wrapper
    return decorator


# ─── Global Cache Instances ────────────────────────────────────────────────────

metrics_cache = RedisCache(prefix="athena:metrics", default_ttl=30)     # 30s for live metrics
prompt_cache  = RedisCache(prefix="athena:prompts", default_ttl=3600)   # 1h for prompt templates
search_cache  = RedisCache(prefix="athena:search",  default_ttl=120)    # 2m for search results
user_cache    = RedisCache(prefix="athena:users",   default_ttl=300)    # 5m for user profiles
