from dataclasses import dataclass
from typing import List
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
    token0_address: str
    token1_address: str
    name: str
@dataclass
class EventSignature:
    signature_hash: str
    name: str
    full_signature: str
    input_types: List[str]
    indexed_inputs: List[bool]
    inputs: List[dict]
    contract_address: str