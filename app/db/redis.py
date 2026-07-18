import os
import redis.asyncio as redis
from typing import Optional
import json

class RedisClient:
    def __init__(self):
        self.url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.pool = None
        self.client = None

    async def connect(self):
        """Initialize the Redis connection pool."""
        try:
            self.pool = redis.ConnectionPool.from_url(self.url)
            self.client = redis.Redis(connection_pool=self.pool)
            # Ping to verify connection
            await self.client.ping()
            print("Connected to Redis")
        except Exception as e:
            print(f"Failed to connect to Redis: {e}")
            self.client = None

    async def close(self):
        """Close the Redis connection."""
        if self.client:
            await self.client.close()
            print("Redis connection closed")

    async def set(self, key: str, value: str, expire: int = 3600):
        if not self.client:
            return
        try:
            await self.client.set(key, value, ex=expire)
        except Exception as e:
            print(f"Redis set error: {e}")

    async def get(self, key: str) -> Optional[str]:
        if not self.client:
            return None
        try:
            val = await self.client.get(key)
            return val.decode("utf-8") if val else None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
            
    def get_client(self):
        return self.client

# Singleton instance
redis_manager = RedisClient()
