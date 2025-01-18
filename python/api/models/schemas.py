from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class BlockResponse(BaseModel):
    network: str
    block_number: int
    block_hash: str
    parent_hash: str
    timestamp: datetime
    transaction_count: Optional[int]

class TransactionResponse(BaseModel):
    network: str
    transaction_hash: str
    block_number: int
    timestamp: datetime
    from_address: Optional[str]
    to_address: Optional[str]
    value: Optional[str]
    
class AnalyticsResponse(BaseModel):
    network: str
    time_period: str
    transaction_count: int
    active_addresses: int
    total_value: float
    patterns: List[Dict[str, Any]]