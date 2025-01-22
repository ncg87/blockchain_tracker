from typing import Dict, List, Optional
from web3 import Web3
from .processors import EventProcessor
from ..models import Transfer

class TransferEventProcessor(EventProcessor):
    def __init__(self):
        super().__init__()

    def process_event(self, event: dict, signature: Optional[str] = None) -> Optional[Transfer]:
        pass
    
    def create_protocol_map(self) -> Dict[str, List[str]]:
        pass
