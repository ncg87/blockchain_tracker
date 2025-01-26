from dataclasses import dataclass
from decimal import Decimal
@dataclass
class SwapEvent:
    network: str
    contract_address: str
    tx_hash: str
    log_index: int
    timestamp: int
    amount0: float
    amount1: float
    token0: str
    token1: str
    amount0_in: bool

@dataclass
class TokenMetadata:
    address: str
    symbol: str
    name: str
    decimals: int

@dataclass
class PairMetrics:
    timestamp: int
    pair_address: str
    token0_address: str
    token1_address: str
    volume_token0: Decimal
    volume_token1: Decimal
    swap_count: int
    unique_addresses: int

@dataclass
class SwapMetadata:
    contract_address: str
    network: str
    token0: str
    token1: str

@dataclass
class IntervalMetrics:
    timestamp: int
    metadata: SwapMetadata
    volume_token0: Decimal
    volume_token1: Decimal
    swap_count: int
    unique_addresses: int