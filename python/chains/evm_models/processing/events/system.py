# Look to migrate this into Rust first, since it is simple but loads of data

from typing import Dict, List, Optional
from .event_processors import SwapProcessor
from database import SQLDatabase, SQLQueryOperations
from operator import itemgetter
import logging
from web3 import Web3

get_event = itemgetter('event')
get_parameters = itemgetter('parameters')
get_type = itemgetter('type')


logger = logging.getLogger(__name__)
class EventProcessingSystem:
    def __init__(self, sql_db: SQLDatabase, mongodb, network):
        self.sql_db = sql_db
        self.mongodb = mongodb
        self.network = network
        self.event_mapping = self.load_event_mapping()
        self.logger = logger
        self.logger.info("EventProcessingSystem initialized")
    def load_event_mapping(self):
        return {
            "Swap": SwapProcessor(self.sql_db, self.network),
        }

    def process_event(self, event: Dict, tx_hash: str, index: int, timestamp: int):
        event_name = get_event(event)
        
        try:
            signature = self.get_signature(event)
            processor = self.event_mapping[event_name]
            
            return processor.process_event(event, signature, tx_hash, index, timestamp)
        except Exception as e:
            #self.logger.error(f"Error processing event: {e}", exc_info=True)
            return None
        
    # pass the function so it doesn't have to look up
    def get_signature(self, event, _keccak=Web3.keccak, _join=','.join):
        name = get_event(event)
        types = tuple(get_type(v) for v in get_parameters(event).values())
        return _keccak(text=name + '(' + _join(types) + ')').hex()