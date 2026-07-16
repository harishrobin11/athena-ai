from typing import Any, Optional
import time
import logging

logger = logging.getLogger(__name__)

# Simple in-memory TTLCache implementation for MVP.
# In a production distributed environment, this would wrap Redis or Memcached.

class TTLCache:
    def __init__(self, ttl_seconds: int = 300):
        self._cache = {}
        self.ttl = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry['timestamp'] < self.ttl:
                logger.debug(f"Cache HIT for key: {key}")
                return entry['data']
            else:
                logger.debug(f"Cache EXPIRED for key: {key}")
                del self._cache[key]
        logger.debug(f"Cache MISS for key: {key}")
        return None

    def set(self, key: str, value: Any):
        self._cache[key] = {
            'data': value,
            'timestamp': time.time()
        }

# Global metric cache instances
metrics_cache = TTLCache(ttl_seconds=60) # Cache metrics for 60 seconds
prompt_cache = TTLCache(ttl_seconds=3600) # Cache static exact-match prompts for 1 hour
