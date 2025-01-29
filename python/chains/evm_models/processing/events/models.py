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
    
    
# future clss for after the contract info is adjusted
"""
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
        amount0 = amount0 / 10 ** contract_info.decimals
        amount1 = amount1 / 10 ** contract_info.decimals
        
        
        # Want this to contain full data, need the contract info to contain the decimals and symbols etc.

        return cls(amount0, 
                   amount1, 
                   contract_info.token0_address, 
                   contract_info.token1_address,
                   contract_info.name,
                   contract_info.factory_address)

"""