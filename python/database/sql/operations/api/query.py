from ..base import BaseOperations
from typing import Dict, List, Any
from ...queries import (
    get_swaps, get_swaps_by_chain
)


class APIQueryOperations(BaseOperations):
    def get_swaps_by_chain(self, chain: str, seconds_ago: int) -> List[Dict[str, Any]]:
        """Get swaps for a specific network within a specific past interval"""
        try:
            query = get_swaps_by_chain(chain, seconds_ago)

            self.db.cursor.execute(query)
            results = self.db.cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            self.db.logger.error(f"Error fetching swaps for interval {chain} past {seconds_ago} seconds: {e}", exc_info=True)
            return []
    
    def get_swaps(self, seconds_ago: int) -> List[Dict[str, Any]]:
        """Get swaps for all networks within a specific past interval"""
        try:
            query = get_swaps(seconds_ago)
            self.db.cursor.execute(query)
            results = self.db.cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            self.db.logger.error(f"Error fetching swaps for all networks for a {seconds_ago} second interval: {e}", exc_info=True)
            return []
