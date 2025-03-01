class SwapCache(BaseRedisCache):
    def __init__(self, **kwargs):
        super().__init__(prefix='swap:', default_ttl=300, **kwargs)  # 5 minutes default TTL

    async def get_recent_swaps(self, pair_id: str, limit: int = 100) -> list:
        """Get recent swaps for a trading pair"""
        key = self._make_key(pair_id, ':recent')
        swaps = await self.redis.lrange(key, 0, limit - 1)
        return [json.loads(swap) for swap in swaps]

    async def add_swap(self, pair_id: str, swap_data: Dict) -> bool:
        """Add a new swap to the recent swaps list"""
        key = self._make_key(pair_id, ':recent')
        await self.redis.lpush(key, json.dumps(swap_data))
        await self.redis.ltrim(key, 0, 999)  # Keep last 1000 swaps
        return True

    async def get_pair_volume(self, pair_id: str, timeframe: str = '24h') -> float:
        """Get trading pair volume"""
        key = self._make_key(pair_id, f':volume:{timeframe}')
        return float(await self.redis.get(key) or 0)

    async def update_pair_volume(self, pair_id: str, volume: float, timeframe: str = '24h') -> None:
        """Update trading pair volume"""
        key = self._make_key(pair_id, f':volume:{timeframe}')
        await self.redis.set(key, volume, ex=86400)  # 24 hour expiry

    async def clear_all(self) -> None:
        """Clear all swap cache data"""
        async for key in self.redis.scan_iter(match=f"{self.prefix}*"):
            await self.redis.delete(key)
        
    async def get_pair_intervals(self, pair_address: str, window_key: str) -> List[Dict]:
        """Get cached intervals for a pair and window"""
        key = f"pair:{pair_address}:window:{window_key}"
        data = await self.redis.get(key)
        return json.loads(data) if data else []

    async def set_pair_intervals(self, pair_address: str, window_key: str, intervals: List[Dict]):
        """Store intervals for a pair and window"""
        key = f"pair:{pair_address}:window:{window_key}"
        await self.redis.set(key, json.dumps(intervals))