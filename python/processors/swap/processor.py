from datetime import datetime, timezone
from typing import List, Dict, DefaultDict
from collections import defaultdict
from base.base_processor import BaseTimeSeriesProcessor
from .metrics import SwapMetrics
from .types import SwapEvent, TokenMetadata, PairMetrics, SwapMetadata, IntervalMetrics
from constants import TimeWindow, TIME_WINDOWS
from decimal import Decimal
import time

class SwapProcessor(BaseTimeSeriesProcessor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metrics = SwapMetrics()
        self.token_metadata_cache = {}  # Cache for token metadata

    
    async def store_swap_data(self, swap_info: SwapEvent):
        try:
            # Key format swap_address:timestamp
            current_timestamp = int(time.time() // 300 * 300)
            key = f"swap_data:{swap_info.contract_address}:{current_timestamp}"

            # Store swap data in Redis
            self.redis_client.hset(
                key,
                mapping={
                    "network": swap_info.network,
                    "token0": swap_info.token0,
                    "token1": swap_info.token1
                }
            )
        except Exception as e:
            logger.error(f"Error storing swap data: {e}")
            
        """Store swap data in Redis"""
        self.redis_client.hset(
            f"swap_data:{swap_info.contract_address}",
            mapping={
                "network": swap_info.network,
                "token0": swap_info.token0,
                "token1": swap_info.token1
            }
        )

    async def _get_token_metadata(self, token_address: str) -> TokenMetadata:
        """Get token metadata from cache or DB"""
        if token_address not in self.token_metadata_cache:
            metadata = await self.db.get_token_metadata(token_address)
            self.token_metadata_cache[token_address] = TokenMetadata(**metadata)
        return self.token_metadata_cache[token_address]

    async def _process_window(self, window_key: str, window: TimeWindow):
        """Process swap data for a specific time window"""
        now = datetime.now(timezone.utc)
        # Only get data for the most recent interval
        interval_seconds = int(window.interval.total_seconds())
        
        # Get raw swap data from DB for just this interval
        raw_swaps = await self.db.get_swaps_all_networks(seconds=interval_seconds)
        
        # Group swaps by contract
        contract_swaps = defaultdict(list)
        for swap in raw_swaps:
            contract_swaps[swap['contract_address']].append(SwapEvent(**swap))
        
        # Process each contract's swaps
        current_timestamp = int(now.timestamp())
        for contract_address, swaps in contract_swaps.items():
            # Calculate metrics for this interval
            metrics = self.metrics.calculate_pair_metrics(
                swaps=swaps,
                timestamp=current_timestamp,
                token_metadata={}  # Add token metadata if needed
            )
            
            # Get existing intervals from cache
            existing_intervals = await self.cache.get_pair_intervals(
                pair_address=contract_address,
                window_key=window_key
            ) or []
            
            # Add new interval
            existing_intervals.append(metrics.__dict__)
            
            # Remove intervals outside the window duration
            window_start = current_timestamp - int(window.duration.total_seconds())
            updated_intervals = [
                interval for interval in existing_intervals
                if interval['timestamp'] >= window_start
            ]
            
            # Store updated intervals in cache
            await self.cache.set_pair_intervals(
                pair_address=contract_address,
                window_key=window_key,
                intervals=updated_intervals
            )

    async def _create_pair_intervals(
        self,
        pair_address: str,
        swaps: List[SwapEvent],
        interval: timedelta,
        start_time: datetime,
        end_time: datetime
    ) -> List[PairMetrics]:
        """Create time intervals with metrics for a specific pair"""
        intervals = []
        current_time = start_time

        # Get token metadata once for the pair
        token0_address = swaps[0].token0
        token1_address = swaps[0].token1
        token_metadata = {
            token0_address: await self._get_token_metadata(token0_address),
            token1_address: await self._get_token_metadata(token1_address)
        }

        while current_time < end_time:
            interval_end = min(current_time + interval, end_time)
            interval_timestamp = int(current_time.timestamp())
            
            # Filter swaps for this interval
            interval_swaps = [
                swap for swap in swaps
                if current_time.timestamp() <= swap.timestamp < interval_end.timestamp()
            ]
            
            # Calculate metrics if we have swaps
            if interval_swaps:
                metrics = self.metrics.calculate_pair_metrics(
                    swaps=interval_swaps,
                    timestamp=interval_timestamp,
                    token_metadata=token_metadata
                )
                intervals.append(metrics)
            else:
                # Add empty interval
                intervals.append(PairMetrics(
                    timestamp=interval_timestamp,
                    pair_address=pair_address,
                    token0_address=token0_address,
                    token1_address=token1_address,
                    volume_token0=Decimal('0'),
                    volume_token1=Decimal('0'),
                    swap_count=0,
                    unique_addresses=0
                ))
            
            current_time += interval

        return intervals

    async def process_new_swap(self, swap_data: Dict):
        """Process a new swap event in real-time"""
        swap = SwapEvent(**swap_data)
        
        # Update all relevant time windows
        for window_key, window in self.time_windows.items():
            current_interval = await self.cache.get_current_pair_interval(
                pair_address=swap.contract_address,
                window_key=window_key
            )
            
            if current_interval:
                # Calculate new metrics including the new swap
                token_metadata = {
                    swap.token0: await self._get_token_metadata(swap.token0),
                    swap.token1: await self._get_token_metadata(swap.token1)
                }
                
                updated_metrics = self.metrics.calculate_pair_metrics(
                    swaps=[swap],
                    timestamp=current_interval.timestamp,
                    token_metadata=token_metadata
                )
                
                # Merge with current metrics
                merged_metrics = PairMetrics(
                    timestamp=current_interval.timestamp,
                    pair_address=swap.contract_address,
                    token0_address=swap.token0,
                    token1_address=swap.token1,
                    volume_token0=current_interval.volume_token0 + updated_metrics.volume_token0,
                    volume_token1=current_interval.volume_token1 + updated_metrics.volume_token1,
                    swap_count=current_interval.swap_count + 1,
                    unique_addresses=current_interval.unique_addresses + 1  # Simplified
                )
                
                # Cache updated metrics
                await self.cache.update_pair_interval(
                    pair_address=swap.contract_address,
                    window_key=window_key,
                    metrics=merged_metrics
                )
