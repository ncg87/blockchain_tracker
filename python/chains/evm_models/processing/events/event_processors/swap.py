from typing import Dict, List, Optional
from web3 import Web3
from ..processors import EventProcessor
from ..models import Swap

class SwapEventProcessor(EventProcessor):
    def get_parameter_mapping(self) -> Dict[str, List[str]]:
        return {
            'from': ['from', 'sender', 'src', 'source', 'fromAddress'],
            'to': ['to', 'recipient', 'dst', 'destination', 'toAddress'],
            'value': ['value', 'amount', 'tokens', 'wad']
        }
    
    def process(self, event: Dict, network: str) -> Optional[Swap]:
        pass