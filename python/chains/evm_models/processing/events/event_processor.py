# Look to migrate this into Rust first, since it is simple but loads of data

from typing import Dict, List, Optional
from .event_processors import SwapProcessor
from database import SQLDatabase
from operator import itemgetter
import logging
from web3 import Web3
from queue import Queue, Empty
import threading
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
        self.pending_threshold = 1000  # Threshold for processing pending events
        
        # Initialize processing queues
        self.event_queue = Queue(maxsize=10000)
        self.result_queue = Queue(maxsize=10000)
        
        # Initialize pending events storage
        self.pending_events = []
        
        # Initialize thread pool
        self._executor = ThreadPoolExecutor(max_workers=8)
        self._shutdown_flag = threading.Event()
        
        # Start background workers
        self._start_processing_workers()
        
        self.logger.info("EventProcessingSystem initialized")

    def _start_processing_workers(self):
        """Start background workers for continuous processing"""
        async def process_worker():
            while not self._shutdown_flag.is_set():
                try:
                    batch_data = self.event_queue.get(timeout=1)
                    if batch_data is None:
                        break
                    events, tx_hash, timestamp = batch_data
                    result = await self._process_events_batch(events, tx_hash, timestamp)
                    self.result_queue.put(result)
                except Empty:
                    continue
                except Exception as e:
                    self.logger.error(f"Worker error: {e}")

        self.workers = []
        for _ in range(8):
            worker = threading.Thread(
                target=lambda: asyncio.run(process_worker()),
                daemon=True
            )
            worker.start()
            self.workers.append(worker)

    def load_event_mapping(self):
        return {
            "Swap": SwapProcessor(self.sql_db, self.network),
        }

    async def process_events(self, events: List[Dict], tx_hash: str, timestamp: int):
        """Process a list of events in parallel"""
        try:
            if not events:
                return []
            
            # Split events into batches
            batches = [events[i:i + self.batch_size] for i in range(0, len(events), self.batch_size)]
            
            # Submit batches to worker queue
            for batch in batches:
                self.event_queue.put((batch, tx_hash, timestamp))
            
            # Collect results and ensure we wait for all batches
            processed_events = []
            for _ in range(len(batches)):
                batch_result = self.result_queue.get(timeout=60)  # Add timeout to prevent hanging
                if batch_result:
                    processed_events.extend(batch_result)
            
            return processed_events
            
        except Exception as e:
            self.logger.error(f"Error processing events: {e}")
            return []

    async def _process_events_batch(self, events: List[Dict], tx_hash: str, timestamp: int):
        """Process a batch of events"""
        processed_events = []
        
        for index, event in enumerate(events):
            try:
                event_name = get_event(event)
                if event_name in self.event_mapping:
                    signature = self.get_signature(event)
                    processor = self.event_mapping[event_name]
                    
                    result = processor.process_event(event, signature, tx_hash, index, timestamp)
                    if result:
                        processed_events.append(result)
                        
            except Exception as e:
                self.logger.error(f"Error processing event: {e}")
                continue
                
        return processed_events

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
            
            processed_results = []
            # Process events directly without accumulating
            for tx_hash, logs in decoded_logs.items():
                if logs:  # Only process if we have logs
                    results = await self.process_events(logs, tx_hash, timestamp)
                    processed_results.extend(results)
            
            return processed_results
                
        except Exception as e:
            self.logger.error(f"Error processing block events: {e}")
            return []

    def shutdown(self):
        """Cleanup method for graceful shutdown"""
        try:
            # Process any remaining pending events
            asyncio.run(self._process_pending_events())
            
            self._shutdown_flag.set()
            
            for _ in self.workers:
                self.event_queue.put(None)
            
            for worker in self.workers:
                worker.join(timeout=60)
            
            self._executor.shutdown(wait=True)
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")