from dataclasses import dataclass
from typing import Optional
@dataclass
class ArbitarySwap:
    amount0: float
    amount1: float
    isAmount0In: bool

@dataclass
class BaseTokenSwap(ArbitarySwap):
    amount0: float
    amount1: float
    isAmount0In: bool
    token0_address: str
    token1_address: str

@dataclass
class TokenSwap(BaseTokenSwap):
    contract_address: str
    token0_name: str
    token1_name: str
    token0_symbol: str
    token1_symbol: str
    token0_address: str
    token1_address: str
    factory_address: Optional[str] = None
    name: Optional[str] = None
    
    @classmethod
    def from_swap_info(cls, swap_info: dict, contract_info: dict):
        
        
        amount0 = swap_info.amount0
        amount1 = swap_info.amount1
        
        amount0In = swap_info.isAmount0In
        
        # Make sure one of the amounts, if one is going in it should be negative
        if amount0In and amount0 > 0:
            amount0 *= -1
        # Check if the amount going in is negative
        if not amount0In and amount1 > 0:
            amount1 *= -1
        # Scale the amounts by the decimals of the token
        amount0 = amount0 / 10 ** contract_info.token0_decimals
        amount1 = amount1 / 10 ** contract_info.token1_decimals
        
        
        # Want this to contain full data, need the contract info to contain the decimals and symbols etc.

        return cls(amount0 = amount0, 
                   amount1 = amount1, 
                   isAmount0In = amount0In,
                   token0_address = contract_info.token0_address, 
                   token1_address = contract_info.token1_address,
                   contract_address = contract_info.address,
                   token0_name = contract_info.token0_name,
                   token1_name = contract_info.token1_name,
                   token0_symbol = contract_info.token0_symbol,
                   token1_symbol = contract_info.token1_symbol,
                   factory_address = contract_info.factory,
                   name = contract_info.name
                   )
    
    @classmethod
    def from_token_info(cls, swap_info: BaseTokenSwap, token_0_info: dict, token_1_info: dict):
        
        amount0 = swap_info.amount0 / 10 ** token_0_info.token0_decimals
        amount1 = swap_info.amount1 / 10 ** token_1_info.token1_decimals
        return cls(amount0 = amount0, 
                   amount1 = amount1, 
                   isAmount0In = swap_info.isAmount0In,
                   token0_address = token_0_info.address, 
                   token1_address = token_1_info.address,
                   contract_address = swap_info.contract_address,
                   factory_address = swap_info.address,
                   token0_name = token_0_info.name,
                   token1_name = token_1_info.name,
                   token0_symbol = token_0_info.symbol,
                   token1_symbol = token_1_info.symbol
                   )

@dataclass
class ArbitaryTransfer:
    amount: float
    isAmountIn: bool
    token: str
@dataclass
class ArbitarySync:
    reserve0: float
    reserve1: float

@dataclass
class TokenSync:
    reserve0: float
    reserve1: float
    token0_address: str
    token1_address: str
    token0_name: str
    token1_name: str
    token0_symbol: str
    token1_symbol: str
    factory_address: str
    name: Optional[str] = None
    

    @classmethod
    def from_sync_info(cls, sync_info: ArbitarySync, contract_info):
        return cls(reserve0 = sync_info.reserve0 / 10 ** contract_info.token0_decimals,
                   reserve1 = sync_info.reserve1 / 10 ** contract_info.token1_decimals,
                   token0_address = contract_info.token0_address,
                   token1_address = contract_info.token1_address,
                   token0_name = contract_info.token0_name,
                   token1_name = contract_info.token1_name,
                   token0_symbol = contract_info.token0_symbol,
                   token1_symbol = contract_info.token1_symbol,
                   factory_address = contract_info.factory,
                   name = contract_info.name)



