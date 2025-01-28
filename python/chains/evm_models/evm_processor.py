from ..base_models import BaseProcessor
from ..utils import decode_hex, normalize_hex
from operator import itemgetter
from abc import abstractmethod
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import json
from queue import Queue, Empty
import threading
from psycopg2.pool import ThreadedConnectionPool
from config import Settings
import signal
import time
import os
from .cache import BoundedCache
from dataclasses import dataclass
import asyncio
from web3 import Web3
from .processing import EventProcessingSystem, BlockProcessor, LogProcessor
from .evm_decoder import EVMDecoder

# Common item getters
get_address = itemgetter('address')
get_transaction_hash = itemgetter('transactionHash')

class EVMProcessor(BaseProcessor):
    """
    Abstract EVM processor class with common functionality.
    """
    def __init__(self, sql_database, mongodb_database, network_name: str, querier):
        super().__init__(sql_database, mongodb_database, network_name)
        self.querier = querier
        self.decoder = EVMDecoder(sql_database, network_name)
        self.event_processor = EventProcessingSystem(sql_database, mongodb_database, network_name)
        self.block_processor = BlockProcessor(self.db_operator, network_name)
        self.log_processor = LogProcessor(self.db_operator, self.querier, network_name)

        # Initialize connection pool
        self.db_pool = ThreadedConnectionPool(
            minconn=5,
            maxconn=20,
            **Settings.POSTGRES_CONFIG
        )
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}. Starting graceful shutdown...")
        self.shutdown()

    def schedule_shutdown(self, delay_seconds=86400):  # Default 24 hours in seconds
        """Schedule an automatic shutdown after specified seconds"""
        def shutdown_timer():
            time.sleep(delay_seconds)
            self.logger.info(f"Automatic shutdown triggered after {delay_seconds} seconds")
            self.shutdown()

        shutdown_thread = threading.Thread(target=shutdown_timer, daemon=True)
        shutdown_thread.start()

    async def process_block(self, block):
        """Process a block, transactions and logs concurrently."""
        try:
            # Get block info immediately - this is synchronous and fast
            block_number, timestamp = self.block_processor.process(block)
            
            # Get logs for the block
            logs = self.querier.get_block_logs(block_number)
            
            # Process logs and get decoded events
            decoded_logs = await self.log_processor.process(block_number, timestamp, logs)
            
            # Process events if we have any decoded logs
            if decoded_logs:
                tasks = [
                    self._process_transaction_events(transaction_hash, logs, timestamp)
                    for transaction_hash, logs in decoded_logs.items()
                ]
                await asyncio.gather(*tasks)
            
        except Exception as e:
            self.logger.error(f"Error processing block {block_number}: {e}", exc_info=True)
            raise
    
    async def _process_transaction_event(self, decoded_event, tx_hash, index, timestamp):
        try:
            return self.event_processor.process_event(decoded_event, tx_hash, index, timestamp)
        except Exception as e:
            self.logger.error(f"Error processing transaction event: {e}", exc_info=True)
            return None
    
    async def _process_transaction_events(self, tx_hash, decoded_logs, timestamp):
        try:
            events = []
            for i, event in enumerate(decoded_logs):
                event_info = await self._process_transaction_event(event, tx_hash, i, timestamp)
                if event_info:
                    events.append(event_info)
            return events
        except Exception as e:
            self.logger.error(f"Error processing transaction events: {e} - {decoded_logs}", exc_info=True)
            
    def shutdown(self):
        """Cleanup method for graceful shutdown"""
        try:
            # Close database pool
            if hasattr(self, 'db_pool'):
                self.db_pool.closeall()
                
            self.logger.info("Processor shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")