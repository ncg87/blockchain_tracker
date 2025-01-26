from dataclasses import dataclass
    
@dataclass
class ArbitarySwap:
    amount0: float
    amount1: float
    isAmount0In: bool
    

@dataclass
class TokenSwap(ArbitarySwap):
    token0: str
    token1: str
    
    @classmethod
    def from_swap_info(cls, swap_info: dict, contract_info: dict):
        return cls(swap_info.amount0, 
                   swap_info.amount1, 
                   swap_info.isAmount0In, 
                   contract_info.token0_address, 
                   contract_info.token1_address)

@dataclass
class ArbitaryTransfer:
    amount: float
    isAmountIn: bool
    token: str

