from typing import List, Dict, Set
from decimal import Decimal
from collections import defaultdict
from .types import SwapEvent, PairMetrics

class SwapMetrics:
    @staticmethod
    def calculate_pair_metrics(
        swaps: List[SwapEvent],
        timestamp: int,
        token_metadata: Dict[str, TokenMetadata]
    ) -> PairMetrics:
        """Calculate metrics for a specific pair"""
        if not swaps:
            return None

        # All swaps should be for the same pair
        pair_address = swaps[0].contract_address
        token0_address = swaps[0].token0
        token1_address = swaps[0].token1
        
        # Calculate volumes
        volume_token0 = Decimal('0')
        volume_token1 = Decimal('0')
        unique_addresses: Set[str] = set()

        for swap in swaps:
            # Add absolute values since amounts can be negative
            volume_token0 += abs(swap.amount0)
            volume_token1 += abs(swap.amount1)
            
            # Track unique addresses from tx_hash (could expand to include actual addresses)
            unique_addresses.add(swap.tx_hash)

        return PairMetrics(
            timestamp=timestamp,
            pair_address=pair_address,
            token0_address=token0_address,
            token1_address=token1_address,
            volume_token0=volume_token0,
            volume_token1=volume_token1,
            swap_count=len(swaps),
            unique_addresses=len(unique_addresses)
        )