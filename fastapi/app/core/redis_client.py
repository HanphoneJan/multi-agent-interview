"""Redis 连接管理"""
import json
from typing import Optional, List, Any
import redis.asyncio as redis

from app.core.config import get_settings

settings = get_settings()

# 全局 Redis 连接池
_redis_pool: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """获取 Redis 连接"""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=50
        )
    return _redis_pool


async def close_redis():
    """关闭 Redis 连接"""
    global _redis_pool
    if _redis_pool:
        await _redis_pool.close()
        _redis_pool = None


class RedisCache:
    """Redis 缓存封装"""

    def __init__(self, redis_client: redis.Redis = None):
        self._redis = redis_client
        self._initialized = redis_client is not None

    async def _ensure_init(self):
        """确保 Redis 连接已初始化"""
        if not self._initialized:
            self._redis = await get_redis()
            self._initialized = True
        return self._redis

    @property
    async def redis(self) -> redis.Redis:
        """获取 Redis 连接（异步属性）"""
        return await self._ensure_init()
    
    async def get(self, key: str) -> Optional[str]:
        """获取字符串值"""
        r = await self.redis
        return await r.get(key)

    async def set(self, key: str, value: str, expire: int = 3600):
        """设置字符串值"""
        r = await self.redis
        await r.set(key, value, ex=expire)

    async def get_json(self, key: str) -> Optional[dict]:
        """获取 JSON 对象"""
        r = await self.redis
        value = await r.get(key)
        return json.loads(value) if value else None

    async def set_json(self, key: str, value: dict, expire: int = 3600):
        """设置 JSON 对象"""
        r = await self.redis
        await r.set(key, json.dumps(value), ex=expire)

    async def hget(self, key: str, field: str) -> Optional[str]:
        """获取 Hash 字段"""
        r = await self.redis
        return await r.hget(key, field)

    async def hset(self, key: str, field: str, value: str):
        """设置 Hash 字段"""
        r = await self.redis
        await r.hset(key, field, value)

    async def hgetall(self, key: str) -> dict:
        """获取所有 Hash 字段"""
        r = await self.redis
        return await r.hgetall(key)

    async def lpush(self, key: str, value: str, max_len: int = 100):
        """列表左侧插入，限制长度"""
        r = await self.redis
        await r.lpush(key, value)
        await r.ltrim(key, 0, max_len - 1)

    async def lrange(self, key: str, start: int = 0, end: int = -1) -> List[str]:
        """获取列表范围"""
        r = await self.redis
        return await r.lrange(key, start, end)

    async def zincrby(self, key: str, amount: float, member: str):
        """有序集合分数增加"""
        r = await self.redis
        await r.zincrby(key, amount, member)

    async def zrevrange(self, key: str, start: int = 0, end: int = -1, withscores: bool = False) -> List[Any]:
        """获取有序集合（降序）"""
        r = await self.redis
        return await r.zrevrange(key, start, end, withscores=withscores)

    async def delete(self, key: str):
        """删除键"""
        r = await self.redis
        await r.delete(key)
