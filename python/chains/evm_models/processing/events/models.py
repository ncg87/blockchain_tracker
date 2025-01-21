from dataclasses import dataclass


@dataclass
class BaseEvent:
    """Base class for all event types"""
    contract_address: str
    
@dataclass
class Transfer(BaseEvent):
    coin: str
    coin_address: str
    coin_symbol: str
    amount: float
    from_address: str
    to_address: str
    
@dataclass
class Swap(BaseEvent):
    from_token: str
    from_amount: float
    from_address: str
    to_token: str
    to_amount: float
    to_address: str