from dataclasses import dataclass
from typing import List, Optional
@dataclass
class TokenInfo:
    address: str
    name: str
    symbol: str
    decimals: int

@dataclass
class ContractInfo:
    address: str
    factory: str
    fee: int
    token0_name: str
    token1_name: str
    token0_symbol: str
    token0_decimals: int
    token1_symbol: str
    token1_decimals: int
    token0_address: str
    token1_address: str
    name: str
@dataclass
class EventSignature:
    signature_hash: str
    event_name: str
    decoded_signature: str
    input_types: List[str]
    indexed_inputs: List[bool]
    input_names: List[str]
    inputs: List[dict]