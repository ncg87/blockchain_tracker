from .base import ClickHouseDB
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

class ClickHouseQueryOperations:
    """
    ClickHouse Query Operations.
    """

    def __init__(self, db: ClickHouseDB):
        self.db = db

    def query_recent_swaps(self, limit: int = 10) -> List[Tuple]:
        """
        Query recent swap transactions.
        """
        query = "SELECT * FROM blockchain_db.dex_swaps ORDER BY timestamp DESC LIMIT %(limit)s;"
        try:
            return self.db.client.execute(query, {'limit': limit})
        except Exception as e:
            logger.error(f"Error querying recent swaps: {e}")
            return []

    def query_swaps_by_chain(self, chain: str, limit: int = 10) -> List[Tuple]:
        """
        Query swap transactions for a specific blockchain.
        """
        query = """
        SELECT * FROM blockchain_db.dex_swaps
        WHERE chain = %(chain)s
        ORDER BY timestamp DESC LIMIT %(limit)s;
        """
        try:
            return self.db.client.execute(query, {'chain': chain, 'limit': limit})
        except Exception as e:
            logger.error(f"Error querying swaps by chain: {e}")
            return []
    def query_by_range_and_chain(self, start_time: int, end_time: int, chain: str) -> List[Tuple]:
        """
        Query swap transactions by timestamp range.
        """
        query = """
        SELECT * FROM blockchain_db.dex_swaps
        WHERE timestamp BETWEEN %(start_time)s AND %(end_time)s
        AND chain = %(chain)s
        ORDER BY timestamp;
        """
        try:
            return self.db.client.execute(query, {'start_time': start_time, 'end_time': end_time, 'limit': limit})
        except Exception as e:
            logger.error(f"Error querying swaps by range: {e}")
            return []
    def query_by_timestamp(self, timestamp: int) -> List[Tuple]:
        """
        Query swap transactions by timestamp.
        """
        query = """
        SELECT * FROM blockchain_db.dex_swaps
        WHERE timestamp = %(timestamp)s
        ORDER BY timestamp;
        """
        try:
            return self.db.client.execute(query, {'timestamp': timestamp})
        except Exception as e:
            logger.error(f"Error querying swaps by timestamp: {e}")
            return []
        

