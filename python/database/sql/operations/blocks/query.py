from ..base import BaseOperations
from ...queries.blocks.query import QUERY_BLOCKS_BY_TIME, QUERY_RECENT_BLOCKS, QUERY_BLOCKS_BY_NETWORK, QUERY_RECENT_BLOCKS_BY_NETWORK
from typing import List, Dict, Any

class BlockQueryOperations(BaseOperations):
    def __init__(self, db):
        super().__init__(db)

    def query_by_time(self, start_time: int, end_time: int) -> List[Dict[str, Any]]:
        """
        Query blocks within a specified time range.
        """
        try:
            self.db.logger.info(f"Querying blocks between {start_time} and {end_time}")
            self.db.cursor.execute(QUERY_BLOCKS_BY_TIME, (start_time, end_time))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying blocks by time: {e}")
            return []
    
    def query_by_network(self, network: str) -> List[Dict[str, Any]]:
        """
        Query blocks by network.
        """
        try:
            self.db.cursor.execute(QUERY_BLOCKS_BY_NETWORK, (network,))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying blocks by network: {e}")
            return []
        
    def query_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Query recent blocks across all networks.
        """
        try:
            self.db.cursor.execute(QUERY_RECENT_BLOCKS, (limit,))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying recent blocks: {e}")
            return []

    def query_recent_by_network(self, network: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Query recent blocks by network.
        """
        try:
            self.db.cursor.execute(QUERY_RECENT_BLOCKS_BY_NETWORK, (network, limit))
            return self.db.cursor.fetchall()
        except Exception as e:
            
            self.db.logger.error(f"Error querying recent blocks by network: {e}")
            return []
