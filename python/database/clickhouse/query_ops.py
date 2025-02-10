from typing import List, Tuple
from .base import ClickHouseDB
import logging

logger = logging.getLogger(__name__)

class ClickHouseInsertOperations:
    """
    ClickHouse Insert Operations.
    """

    def __init__(self, db: ClickHouseDB):
        self.db = db

    def insert_bulk_swaps(self, swaps: List[Tuple[int, str, str, str, str, str, str, str, float]]):
        """
        Bulk insert swap transactions into ClickHouse.
        
        :param swaps: List of tuples (timestamp, chain, dex, factory_id, from_coin_symbol, from_coin_address, to_coin_symbol, to_coin_address, price_from)
        """
        query = f"""
        INSERT INTO {self.db.database}.dex_swaps
        (timestamp, chain, dex, factory_id, from_coin_symbol, from_coin_address, to_coin_symbol, to_coin_address, price_from)
        VALUES
        """
        try:
            self.db.client.execute(query, swaps)
            logger.info(f"Inserted {len(swaps)} swap records into ClickHouse.")
        except Exception as e:
            logger.error(f"Error inserting swaps: {e}")
            raise
