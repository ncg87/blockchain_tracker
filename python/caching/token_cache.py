class TokenCache(BaseRedisCache):
    def __init__(self, **kwargs):
        super().__init__(prefix='token:', default_ttl=3600, **kwargs)  # 1 hour default TTL

    async def get_token_data(self, address: str) -> Optional[Dict]:
        """Get basic token data"""
        return await self._get(address)

    async def set_token_data(self, address: str, data: Dict, ttl: int = None) -> bool:
        """Set basic token data"""
        return await self._set(address, data, ttl)

    async def get_token_volume(self, address: str, timeframe: str = '24h') -> float:
        """Get token volume for a specific timeframe"""
        key = self._make_key(address, f':volume:{timeframe}')
        return float(await self.redis.get(key) or 0)

    async def update_token_volume(self, address: str, volume: float, timeframe: str = '24h') -> None:
        """Update token volume"""
        key = self._make_key(address, f':volume:{timeframe}')
        await self.redis.set(key, volume, ex=86400)  # 24 hour expiry for volume

    async def get_top_tokens(self, limit: int = 100) -> list:
        """Get top tokens by volume"""
        return await self.redis.zrevrange('token:top_by_volume', 0, limit-1)

    async def clear_all(self) -> None:
        """Clear all token cache data"""
        async for key in self.redis.scan_iter(match=f"{self.prefix}*"):
            await self.redis.delete(key)