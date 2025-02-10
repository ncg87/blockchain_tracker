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

    async def insert_swaps(self, records: List[Dict]):
        """
        Insert swap records into ClickHouse.
        """
        query = """
        INSERT INTO blockchain_db.dex_swaps
        (timestamp, chain, dex, factory_id, from_coin_symbol, from_coin_address, 
         to_coin_symbol, to_coin_address, price_from)
        VALUES
        """
        try:
            # Convert records to tuples in the correct order
            values = [
                (
                    r['timestamp'],
                    r['chain'],
                    r['dex'],
                    r['factory_id'],
                    r['from_coin_symbol'],
                    r['from_coin_address'],
                    r['to_coin_symbol'],
                    r['to_coin_address'],
                    r['price_from']
                )
                for r in records
            ]
            
            await self.db.client.execute(query, values)
            logger.info(f"Inserted {len(records)} swap records into ClickHouse")
            return True
        except Exception as e:
            logger.error(f"Error inserting swaps into ClickHouse: {e}")
            return False

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
