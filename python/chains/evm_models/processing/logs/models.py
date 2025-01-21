from dataclasses import dataclass

@dataclass
class TokenInfo:
    address: str
    name: str
    symbol: str

@dataclass
class ContractInfo:
    address: str
    factory: str
    fee: int
    token0_name: str
    token1_name: str
    name: str