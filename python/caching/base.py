from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import redis.asyncio as redis
import json
from datetime import datetime

class BaseRedisCache(ABC):
    def __init__(
        self,
        redis_client: redis.Redis = None,
        host: str = 'localhost',
        port: int = 6379,
        default_ttl: int = 300,
        prefix: str = ''
    ):
        self.redis = redis_client or redis.Redis(
            host=host,
            port=port,
            decode_responses=True,
            socket_timeout=5
        )
        self.default_ttl = default_ttl
        self.prefix = prefix

    def _make_key(self, key: str, suffix: str = '') -> str:
        """Create a namespaced key"""
        return f"{self.prefix}{key}{suffix}"

    async def _get(self, key: str) -> Optional[Any]:
        """Base get method with JSON deserialization"""
        data = await self.redis.get(self._make_key(key))
        return json.loads(data) if data else None

    async def _set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Base set method with JSON serialization"""
        return await self.redis.set(
            self._make_key(key),
            json.dumps(value),
            ex=(ttl or self.default_ttl)
        )

    async def _delete(self, key: str) -> bool:
        """Base delete method"""
        return bool(await self.redis.delete(self._make_key(key)))

    @abstractmethod
    async def clear_all(self) -> None:
        """Clear all cached data for this cache type"""