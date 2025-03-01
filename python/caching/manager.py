
import redis.asyncio as redis
from typing import Optional
from .token_cache import TokenCache
from .swap_cache import SwapCache

class CacheManager:
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        password: Optional[str] = None,
        db: int = 0
    ):
        # Create Redis connection
        self.redis = redis.Redis(
            host=host,
            port=port,
            password=password,
            db=db,
            decode_responses=True,
            socket_timeout=5
        )
        
        # Initialize caches
        self.tokens = TokenCache(redis_client=self.redis)
        self.swaps = SwapCache(redis_client=self.redis)

    async def get_redis_info(self) -> dict:
        """Get Redis server information"""
        return await self.redis.info()

    async def get_memory_usage(self) -> dict:
        """Get memory usage statistics"""
        info = await self.redis.info('memory')
        return {
            'used_memory': info['used_memory_human'],
            'peak_memory': info['used_memory_peak_human'],
            'fragmentation_ratio': info['mem_fragmentation_ratio']
        }

    async def clear_all(self):
        """Clear all caches"""
        await self.tokens.clear_all()
        await self.swaps.clear_all()

    async def health_check(self) -> bool:
        """Check if Redis connection is healthy"""
        try:
            await self.redis.ping()
            return True
        except redis.RedisError:
            return False

    async def close(self):
        """Close Redis connection"""
        await self.redis.close()