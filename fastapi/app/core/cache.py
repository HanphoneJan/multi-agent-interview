"""Redis cache management"""
import json
import asyncio
from typing import Any, Optional

import redis.asyncio as redis

from app.config import get_settings

settings = get_settings()


class RedisCache:
    """Redis cache manager"""

    def __init__(self):
        self._pool = None
        self._redis = None

    async def connect(self):
        """Connect to Redis"""
        if self._redis is None:
            self._pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=settings.REDIS_POOL_SIZE,
                decode_responses=True
            )
            self._redis = redis.Redis(connection_pool=self._pool)

    async def disconnect(self):
        """Disconnect from Redis"""
        if self._redis:
            await self._redis.aclose()
            self._redis = None
            self._pool = None

    async def _execute_with_retry(self, method_name_or_func, *args, **kwargs):
        """Execute Redis operation with reconnection on failure

        Args:
            method_name_or_func: Either a method name string (e.g., "get", "set")
                                 or a callable function for complex operations
        """
        async def _do_execute():
            if not self._redis:
                await self.connect()

            if callable(method_name_or_func):
                # It's a function (like pipeline_execute callback)
                return await method_name_or_func(self._redis)
            else:
                # It's a method name string
                method = getattr(self._redis, method_name_or_func)
                return await method(*args, **kwargs)

        try:
            return await _do_execute()
        except (RuntimeError, ConnectionError, OSError):
            # Connection lost (e.g., event loop closed), reconnect and retry once
            await self.disconnect()
            return await _do_execute()

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        return await self._execute_with_retry("get", key)

    async def set(
        self,
        key: str,
        value: str | int | float | dict | list,
        ex: Optional[int] = None
    ):
        """Set value in cache"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        else:
            value = str(value)

        return await self._execute_with_retry("set", key, value, ex=ex)

    async def delete(self, key: str):
        """Delete key from cache"""
        return await self._execute_with_retry("delete", key)

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        result = await self._execute_with_retry("exists", key)
        return result > 0

    async def ttl(self, key: str) -> int:
        """Get remaining time to live for a key in seconds

        Returns:
            -2 if key does not exist
            -1 if key exists but has no TTL
            >= 0 remaining seconds
        """
        return await self._execute_with_retry("ttl", key)

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for a key

        Returns:
            True if timeout was set, False if key does not exist
        """
        return await self._execute_with_retry("expire", key, seconds)

    async def incr(self, key: str) -> int:
        """Increment the integer value of a key by 1

        Returns:
            New value after increment
        """
        return await self._execute_with_retry("incr", key)

    async def incrby(self, key: str, amount: int) -> int:
        """Increment the integer value of a key by given amount

        Returns:
            New value after increment
        """
        return await self._execute_with_retry("incrby", key, amount)

    async def get_many(self, keys: list[str]) -> dict[str, str]:
        """Get multiple values from cache"""
        values = await self._execute_with_retry("mget", keys)
        return {k: v for k, v in zip(keys, values) if v is not None}

    async def set_many(self, mapping: dict[str, str], ex: Optional[int] = None):
        """Set multiple values in cache"""
        async def _pipe_execute(redis_client):
            pipe = redis_client.pipeline()
            for key, value in mapping.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                else:
                    value = str(value)
                pipe.set(key, value, ex=ex)
            return await pipe.execute()

        return await self._execute_with_retry("pipeline_execute", _pipe_execute)

    async def get_or_set(
        self,
        key: str,
        value_func,
        ex: Optional[int] = None
    ) -> str:
        """Get value from cache or set using value_func"""
        cached = await self.get(key)
        if cached is not None:
            return cached

        value = await value_func()
        await self.set(key, value, ex=ex)
        return value


# Global cache instance
cache = RedisCache()
