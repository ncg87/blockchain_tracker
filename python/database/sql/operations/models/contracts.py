from dataclasses import dataclass

@dataclass
class ContractInfo:
    address: str
    factory: str
    fee: int
    token0_name: str
    token1_name: str
    token0_symbol: str
    token1_symbol: str
    token0_decimals: int
    token1_decimals: int
    token0_address: str
    token1_address: str
    name: str