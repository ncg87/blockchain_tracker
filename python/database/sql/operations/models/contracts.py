from dataclasses import dataclass

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