# Look to migrate this into Rust first, since it is simple but loads of data

from typing import Dict, List
from .event_processors import SwapProcessor, SyncProcessor
from database import DatabaseOperator, ClickHouseOperator, ClickHouseDB, ArcticOperator, ArcticDB
from operator import itemgetter
import logging
from web3 import Web3
import asyncio
import numpy as np
from time import time



get_event = itemgetter('event')
get_parameters = itemgetter('parameters')
get_type = itemgetter('type')

logger = logging.getLogger(__name__)

class EventProcessor:
    def __init__(self, db_operator : DatabaseOperator, chain : str):
        self.db_operator = db_operator
        self.chain = chain
        self.event_mapping = self.load_event_mapping()
        self.logger = logger
        self.batch_size = 1000
        self.arctic = ArcticOperator(ArcticDB())
        self.logger.info("EventProcessor initialized")

    def load_event_mapping(self):

        return {
            "Swap": SwapProcessor(self.db_operator, self.chain),
            "Sync": SyncProcessor(self.db_operator, self.chain),
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
            if event_name not in self.event_mapping:
                return None
                
            signature = self.get_signature(event)
            processor = self.event_mapping[event_name]
            processed_event = processor.process_event(event, signature, tx_hash, index, timestamp)
            
            if not processed_event:
                return None
            
            # Handle sync events directly
            if event_name == "Sync":
                await self.handle_sync_event(processed_event, timestamp)
                
            return processed_event
            
        except Exception as e:
            self.logger.error(f"Error processing event: {e}", exc_info=True)
            return None

    def get_signature(self, event, _keccak=Web3.keccak, _join=','.join):
        """Get event signature using cached functions"""
        name = get_event(event)
        types = tuple(get_type(v) for v in get_parameters(event).values())
        return _keccak(text=name + '(' + _join(types) + ')').hex()

    async def handle_sync_event(self, sync, timestamp: int):
        """Process a sync event and insert price records"""
        try:
            if sync.factory_address not in FEE_MAP:
                return
                
            fee = FEE_MAP[sync.factory_address]
            dex = DEX_MAP[sync.factory_address]

            # Create records for both directions
            records = [
                {
                    'timestamp': timestamp,
                    'chain': self.chain,
                    'dex': dex,
                    'factory_id': sync.factory_address,
                    'from_coin_symbol': sync.token0_symbol,
                    'from_coin_address': sync.token0_address,
                    'to_coin_symbol': sync.token1_symbol,
                    'to_coin_address': sync.token1_address,
                    'contract_address': sync.contract_address,
                    'price_from': self.calculate_price(fee, sync.reserve0, sync.reserve1)
                },
                {
                    'timestamp': timestamp,
                    'chain': self.chain,
                    'dex': dex,
                    'factory_id': sync.factory_address,
                    'from_coin_symbol': sync.token1_symbol,
                    'from_coin_address': sync.token1_address,
                    'to_coin_symbol': sync.token0_symbol,
                    'to_coin_address': sync.token0_address,
                    'contract_address': sync.contract_address,
                    'price_from': self.calculate_price(fee, sync.reserve1, sync.reserve0)
                }
            ]
            
            # Insert into database
            await self.arctic.insert.swaps(records)
            
        except Exception as e:
            self.logger.error(f"Error processing sync event: {e}")

    def calculate_price(self, fee: float, reserve_from: float, reserve_to: float) -> float:
        """Calculate price using the same formula as swap_analysis"""
        return np.log(reserve_from * (1 - fee) / reserve_to)

    async def process_block_events(self, decoded_logs: Dict[str, List[Dict]], timestamp: int):
        """Process all events from a block's decoded logs"""
        try:
            if not decoded_logs:
                return []
            
            # Process all transactions concurrently
            tasks = [
                self.process_events(logs, tx_hash, timestamp)
                for tx_hash, logs in decoded_logs.items()
                if logs
            ]
            
            if not tasks:
                return []
            
            # Wait for all transaction processing to complete
            results = await asyncio.gather(*tasks)
            
            # Flatten results
            return [item for sublist in results if sublist for item in sublist]
                
        except Exception as e:
            self.logger.error(f"Error processing block events: {e}")
            return []

FEE_MAP = {
    '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f': 0.003,
    '0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac': 0.003,
    '0x1097053Fd2ea711dad45caCcc45EfF7548fCB362': 0.0025,
}

DEX_MAP = {
    '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f' : 'Uniswap V2',
    '0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac' : 'SushiSwap',
    '0x1097053Fd2ea711dad45caCcc45EfF7548fCB362' : 'PancakeSwapV2',
    '0x115934131916C8b277DD010Ee02de363c09d037c' : 'ShibaSwap',
    '0x75e48C954594d64ef9613AeEF97Ad85370F13807' : 'SakeSwap', 
    '0x9DEB29c9a4c7A88a3C0257393b7f3335338D9A9D' : 'DeFiSwap',
    '0xee3E9E46E34a27dC755a63e2849C9913Ee1A06E2' : 'WiseSwap', #??
    '0x4eef5746ED22A2fD368629C1852365bf5dcb79f1' : 'Future Lithuim', # ??
    '0xcBAE5C3f8259181EB7E2309BC4c72fDF02dD56D8' : 'NineInch', # ??
    
}
