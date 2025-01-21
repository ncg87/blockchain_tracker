from typing import Dict, List, Optional
from .models import BaseEvent
from .registry import EventProcessorRegistry

class EventProcessingSystem:
    def __init__(self, sql_query_ops=None):
        self.sql_query_ops = sql_query_ops
        self.registry = EventProcessorRegistry.create_default_registry(sql_query_ops)

    def process_event(self, event: Dict, network: str) -> Optional[BaseEvent]:
        event_name = event['event']
        event_signature = event.get('event_signature')
        
        if not event_signature:
            return None
            
        processor = self.registry.get_processor(event_name, event_signature)
        if processor is None:
            return None
            
        return processor.process(event, network)

    def process_transaction_events(self, transaction_data: List[Dict], network: str) -> Dict[str, List[BaseEvent]]:
        processed_events = {}
        
        for item in transaction_data:
            tx_hash = item['transaction_hash']
            processed_events[tx_hash] = []
            
            for event in item['log_data']:
                processed_event = self.process_event(event, network)
                if processed_event:
                    processed_events[tx_hash].append(processed_event)
                    
        return processed_events