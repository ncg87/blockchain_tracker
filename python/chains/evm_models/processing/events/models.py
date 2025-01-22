from dataclasses import dataclass
    
@dataclass
class ArbitarySwap:
    amount0: float
    amount1: float
    isAmount0In: bool
    

@dataclass
class ArbitaryTransfer:
    amount: float
    isAmountIn: bool
    token: str

