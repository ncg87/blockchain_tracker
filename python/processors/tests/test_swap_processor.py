import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from swap import SwapProcessor, SwapEvent, SwapMetadata

# Mock Redis Cache
class MockRedisCache:
    def __init__(self):
        self.cache = {}
    
    async def get_pair_intervals(self, pair_address: str, window_key: str):
        key = f"pair:{pair_address}:window:{window_key}"
        return self.cache.get(key, [])
    
    async def set_pair_intervals(self, pair_address: str, window_key: str, intervals):
        key = f"pair:{pair_address}:window:{window_key}"
        self.cache[key] = intervals
        print(f"Cached {len(intervals)} intervals for {pair_address} in {window_key} window")

# Mock DB Client
class MockDBClient:
    async def get_swaps_all_networks(self, seconds: int):
        # Return some test swap data
        return [
            {
                'network': 'Arbitrum',
                'contract_address': '0x0BaCc7a9717e70EA0DA5Ac075889Bd87d4C81197',
                'tx_hash': '0x7be8cfb7821767e22adf2323e287230f1a417855e624c938a8477ad18e501f95',
                'log_index': 2,
                'timestamp': int(datetime.now(timezone.utc).timestamp()),
                'amount0': Decimal('-142079629799526173'),
                'amount1': Decimal('473124645'),
                'token0': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
                'token1': '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
                'amount0_in': True
            },
            {
                'network': 'Arbitrum',
                'contract_address': '0x0BaCc7a9717e70EA0DA5Ac075889Bd87d4C81197',
                'tx_hash': '0x8ce8cfb7821767e22adf2323e287230f1a417855e624c938a8477ad18e501f96',
                'log_index': 3,
                'timestamp': int(datetime.now(timezone.utc).timestamp()),
                'amount0': Decimal('-242079629799526173'),
                'amount1': Decimal('573124645'),
                'token0': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
                'token1': '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
                'amount0_in': True
            }
        ]

async def test_swap_processor():
    # Initialize mocks
    cache = MockRedisCache()
    db = MockDBClient()
    
    # Create processor
    processor = SwapProcessor(
        cache_manager=cache,
        db_client=db
    )
    
    # Process a single window
    window_key = '5m'
    window = processor.time_windows[window_key]
    await processor._process_window(window_key, window)
    
    # Print cached data
    for key, value in cache.cache.items():
        print(f"\nCache key: {key}")
        print("Intervals:")
        for interval in value:
            print(f"  Timestamp: {interval['timestamp']}")
            print(f"  Volume Token0: {interval['volume_token0']}")
            print(f"  Volume Token1: {interval['volume_token1']}")
            print(f"  Swap Count: {interval['swap_count']}")
            print(f"  Unique Addresses: {interval['unique_addresses']}")

if __name__ == "__main__":
    asyncio.run(test_swap_processor()) 