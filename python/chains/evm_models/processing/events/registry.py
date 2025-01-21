from typing import Dict, Optional
from .processors import EventProcessor
from .event_processors import TransferEventProcessor, SwapEventProcessor

class EventProcessorRegistry:
    def __init__(self):
        self._processors: Dict[str, Dict[str, EventProcessor]] = {}
        
    def register_processor(self, event_name: str, signature: str, processor: EventProcessor):
        if event_name not in self._processors:
            self._processors[event_name] = {}
        self._processors[event_name][signature] = processor

    def get_processor(self, event_name: str, signature: str) -> Optional[EventProcessor]:
        if event_name in self._processors:
            return self._processors[event_name].get(signature)
        return None

    @classmethod
    def create_default_registry(cls, sql_query_ops=None) -> 'EventProcessorRegistry':
        registry = cls()
        registry.register_processor(
            'Transfer',
            'Transfer(address,address,uint256)',
            TransferEventProcessor(sql_query_ops)
        )
        # Add more default processors here
        return registry