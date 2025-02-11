# Look to migrate this into Rust first, since it is simple but loads of data

from typing import Dict, List
from .event_processors import SwapProcessor, SyncProcessor
from database import DatabaseOperator
from operator import itemgetter
import logging
from web3 import Web3
import asyncio
import numpy as np
from time import time
import math



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

            # Create tuples for both directions matching schema order
            records = [
                (self.chain, timestamp, sync.factory_address, sync.contract_address,
                 sync.token0_symbol, sync.token0_address,
                 sync.token1_symbol, sync.token1_address,
                 self.calculate_price(fee, sync.reserve0, sync.reserve1),
                 float(sync.reserve0), float(sync.reserve1), fee),
                
                (self.chain, timestamp, sync.factory_address, sync.contract_address,
                 sync.token1_symbol, sync.token1_address,
                 sync.token0_symbol, sync.token0_address,
                 self.calculate_price(fee, sync.reserve1, sync.reserve0),
                 float(sync.reserve1), float(sync.reserve0), fee)
            ]
            
            # Insert both records at once
            self.db_operator.clickhouse.insert.price_record(self.chain, records)
            
        except Exception as e:
            self.logger.error(f"Error inserting prices into ClickHouse: {e}")

    def calculate_price(self, fee: float, reserve_from: float, reserve_to: float) -> float:
        """Calculate price using standard math instead of numpy"""
        try:
            if reserve_to == 0:
                return 0.0
            return - math.log(reserve_from * (1 - fee) / reserve_to)
        except (ValueError, ZeroDivisionError):
            return 0.0

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
    '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f': 0.003,  # Uniswap V2
    '0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac': 0.003,  # SushiSwap V2
    '0x1097053Fd2ea711dad45caCcc45EfF7548fCB362': 0.0025, # PancakeSwap V2
    
    '0x115934131916C8b277DD010Ee02de363c09d037c': 0.003,  # ShibaSwap V2
    '0x75e48C954594d64ef9613AeEF97Ad85370F13807': 0.003,  # SakeSwap V2
    '0x4eef5746ED22A2fD368629C1852365bf5dcb79f1': 0.003,  # Future Lithium
    '0x5D8d3bbE66076e844C82B989F8430Fa92Cf67DBA': 0.003,  # BitBerry V2
    '0x9DEB29c9a4c7A88a3C0257393b7f3335338D9A9D': 0.003,  # DeFiSwap
    '0xd34971BaB6E5E356fd250715F5dE0492BB070452': 0.003,  # DXSwaps V2
    '0xF14421F0BCf9401d8930872C2d44d8e67e40529a': 0.003,  # Equalizer V2
    '0x43eC799eAdd63848443E2347C49f5f52e8Fe0F6f': 0.003,  # FraxSwap V2
    '0xBAe5dc9B19004883d0377419FeF3c2C8832d7d7B': 0.003,  # ApeSwap V2
    '0x5FA0060FcfEa35B31F7A5f6025F0fF399b98Edf1': 0.003,  # OrionProtocol V2
    '0x91fAe1bc94A9793708fbc66aDcb59087C46dEe10': 0.003,  # RadioShackSwap V2
    '0xd674b01E778CF43D3E6544985F893355F46A74A5': 0.003,  # EmpireSwap V2

    '0xd87Ad19db2c4cCbf897106dE034D52e3DD90ea60': 0.003,  # PlasmaSwap V2
    '0x696708Db871B77355d6C2bE7290B27CF0Bb9B24b': 0.003,  # LinkSwap V2
    '0x19E5ebC005688466d11015e646Fa182621c1881e': 0.003,  # SaitaSwap V2
    '0x8a93B6865C4492fF17252219B87eA6920848EdC0': 0.003,  # SwipeSwap V2
    '0xcDc7c1d7542128d96fb944AF966EA1be5CE31fca': 0.003,  # KingSwap V2

    '0x03407772F5EBFB9B10Df007A2DD6FFf4EdE47B53': 0.003,  # Capital V2
    '0x93F9a2765245fBeF39bC1aE79aCbe0222b524080': 0.003,  # P00ls V2
    '0x0388C1E0f210AbAe597B7DE712B9510C6C36C857': 0.003,  # luaSwap V2
    '0x5326a41E17037cdab5737eF372b7C04DDEc1eCe6': 0.003,  # WallStreetBets V2

    '0xee3E9E46E34a27dC755a63e2849C9913Ee1A06E2': 0.003,  # WiseSwap (assuming Uniswap V2 fork)
    '0xcBAE5C3f8259181EB7E2309BC4c72fDF02dD56D8': 0.003,  # NineInch (assuming Uniswap V2 fork)
}


DEX_MAP = {
    '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f' : 'Uniswap V2',
    '0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac' : 'SushiSwapV2',
    '0x1097053Fd2ea711dad45caCcc45EfF7548fCB362' : 'PancakeSwapV2',
    '0x115934131916C8b277DD010Ee02de363c09d037c' : 'ShibaSwapV2',
    '0x75e48C954594d64ef9613AeEF97Ad85370F13807' : 'SakeSwapV2', 
    '0x4eef5746ED22A2fD368629C1852365bf5dcb79f1' : 'Future Lithuim',
    '0x5D8d3bbE66076e844C82B989F8430Fa92Cf67DBA' : 'BitBerryV2',
    '0x9DEB29c9a4c7A88a3C0257393b7f3335338D9A9D' : 'DeFiSwap',
    '0xd34971BaB6E5E356fd250715F5dE0492BB070452' : 'DXSwapsV2',
    '0xF14421F0BCf9401d8930872C2d44d8e67e40529a' : 'EqualizerV2',
    '0x43eC799eAdd63848443E2347C49f5f52e8Fe0F6f' : 'FraxSwapV2',
    '0xBAe5dc9B19004883d0377419FeF3c2C8832d7d7B' : 'ApeSwapV2',
    '0x5FA0060FcfEa35B31F7A5f6025F0fF399b98Edf1' : 'OrionProtocolV2',
    '0x91fAe1bc94A9793708fbc66aDcb59087C46dEe10' : 'RadioShackSwapV2',
    '0xd674b01E778CF43D3E6544985F893355F46A74A5' : 'EmpireSwapV2',
    
    '0xd87Ad19db2c4cCbf897106dE034D52e3DD90ea60' : 'PlasmaSwapV2',
    '0x696708Db871B77355d6C2bE7290B27CF0Bb9B24b' : 'LinkSwapV2',
    '0x19E5ebC005688466d11015e646Fa182621c1881e' : 'SaitaSwapV2',
    '0x8a93B6865C4492fF17252219B87eA6920848EdC0' : 'SwipeSwapV2',
    '0xcDc7c1d7542128d96fb944AF966EA1be5CE31fca' : 'KingSwapV2',
    
    '0x03407772F5EBFB9B10Df007A2DD6FFf4EdE47B53' : 'CapitalV2',
    '0x93F9a2765245fBeF39bC1aE79aCbe0222b524080' : 'P00lsV2',
    '0x0388C1E0f210AbAe597B7DE712B9510C6C36C857' : 'luaSwapV2',
    '0x5326a41E17037cdab5737eF372b7C04DDEc1eCe6' : 'WallStreetBetsV2',
    
    '0xee3E9E46E34a27dC755a63e2849C9913Ee1A06E2' : 'WiseSwap', #??
    '0xcBAE5C3f8259181EB7E2309BC4c72fDF02dD56D8' : 'NineInch', # ??
    
}
