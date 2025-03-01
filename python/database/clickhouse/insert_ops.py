from typing import List, Tuple, Dict
from .base import ClickHouseDB
import logging

logger = logging.getLogger(__name__)

class ClickHouseInsertOperations:
    """
    ClickHouse Insert Operations.
    """

    def __init__(self, db: ClickHouseDB):
        self.db = db

    def block_timestamp(self, chain: str, timestamp: int, block_number: int):
        """
        Insert a single block timestamp record into ClickHouse.
        
        :param chain: Blockchain identifier string
        :param timestamp: Unix timestamp as UInt32
        :param block_number: Block number as UInt64
        """
        query = """
        INSERT INTO blockchain_db.block_timestamps
        (chain, timestamp, block_number)
        VALUES
        """
        try:
            self.db.client.execute(
                query, 
                [(chain, timestamp, block_number)],
                settings={
                    'async_insert': 1,
                    'wait_for_async_insert': 0
                }
            )
            logger.info(f"Queued block timestamp for chain {chain}, block {block_number}")
            return True
        except Exception as e:
            logger.error(f"Error inserting block timestamp into ClickHouse: {e}")
            return False

    def price_record(self, chain: str, records: List[Tuple]):
        """
        Insert multiple price records into ClickHouse.
        
        :param chain: Blockchain identifier string
        :param records: List of tuples with values in schema order:
                       (chain, timestamp, log_index, factory_id, contract_id,
                        from_coin_symbol, from_coin_address,
                        to_coin_symbol, to_coin_address,
                        price_from, reserve_from, reserve_to, fees)
        """
        query = """
        INSERT INTO blockchain_db.dex_prices
        (chain, timestamp, log_index, factory_id, contract_id,
         from_coin_symbol, from_coin_address,
         to_coin_symbol, to_coin_address,
         price_from, reserve_from, reserve_to, fees)
        VALUES
        """
        try:
            self.db.client.execute(
                query, 
                records,
                settings={
                    'async_insert': 1,
                    'wait_for_async_insert': 0
                    
                }
            )
            logger.info(f"Inserted {len(records)} price records for chain {chain}")
            return True
        except Exception as e:
            logger.error(f"Error inserting prices into ClickHouse: {e}")
            return False