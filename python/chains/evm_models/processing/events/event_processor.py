# Look to migrate this into Rust first, since it is simple but loads of data

from typing import Dict, List, Optional
from .event_processors import SwapProcessor
from database import SQLDatabase
from operator import itemgetter
import logging
from web3 import Web3
from concurrent.futures import ThreadPoolExecutor
import asyncio
from collections import defaultdict

get_event = itemgetter('event')
get_parameters = itemgetter('parameters')
get_type = itemgetter('type')

logger = logging.getLogger(__name__)

class EventProcessor:
    def __init__(self, sql_db: SQLDatabase, mongodb, network):
        self.sql_db = sql_db
        self.mongodb = mongodb
        self.network = network
        self.event_mapping = self.load_event_mapping()
        self.logger = logger
        self.batch_size = 1000
        
        self.logger.info("EventProcessingSystem initialized")

    def load_event_mapping(self):
        return {
            "Swap": SwapProcessor(self.sql_db, self.network),
        }

    async def process_events(self, events: List[Dict], tx_hash: str, timestamp: int):
        """Process a list of events using pure asyncio"""
        try:
            if not events:
                return []
            
            # Split events into batches
            batches = [events[i:i + self.batch_size] for i in range(0, len(events), self.batch_size)]
            
            # Process all batches concurrently
            tasks = [self._process_events_batch(batch, tx_hash, timestamp) for batch in batches]
            batch_results = await asyncio.gather(*tasks)
            
            # Combine results
            return [result for batch in batch_results if batch for result in batch]
            
        except Exception as e:
            self.logger.error(f"Error processing events: {e}")
            return []

    async def _process_events_batch(self, events: List[Dict], tx_hash: str, timestamp: int):
        """Process a batch of events concurrently"""
        try:
            tasks = [
                self._process_single_event(event, tx_hash, index, timestamp)
                for index, event in enumerate(events)
            ]
            results = await asyncio.gather(*tasks)
            return [result for result in results if result is not None]
                
        except Exception as e:
            self.logger.error(f"Error processing event batch: {e}")
            return []

    async def _process_single_event(self, event: Dict, tx_hash: str, index: int, timestamp: int):
        """Process a single event"""
        try:
            event_name = get_event(event)
            if event_name in self.event_mapping:
                signature = self.get_signature(event)
                processor = self.event_mapping[event_name]
                
                return processor.process_event(event, signature, tx_hash, index, timestamp)
                    
        except Exception as e:
            self.logger.error(f"Error processing event: {e}")
            return None

    def get_signature(self, event, _keccak=Web3.keccak, _join=','.join):
        """Get event signature using cached functions"""
        name = get_event(event)
        types = tuple(get_type(v) for v in get_parameters(event).values())
        return _keccak(text=name + '(' + _join(types) + ')').hex()

    async def process_block_events(self, decoded_logs: Dict[str, List[Dict]], timestamp: int):
        """Process all events from a block's decoded logs"""
        try:
            if not decoded_logs:
                return
            
            # Create tasks for each transaction's events
            tasks = []
            for tx_hash, logs in decoded_logs.items():
                if logs:  # Only process if we have logs
                    tasks.append(self.process_events(logs, tx_hash, timestamp))
            
            # Process all transactions concurrently
            results = await asyncio.gather(*tasks)
            
            # Combine results from all transactions
            processed_results = []
            for result in results:
                if result:
                    processed_results.extend(result)
            
            return processed_results
                
        except Exception as e:
            self.logger.error(f"Error processing block events: {e}")
            return []

    def shutdown(self):
        """Cleanup method for graceful shutdown"""
        try:
            self._executor.shutdown(wait=True)
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")