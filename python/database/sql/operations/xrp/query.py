from ...queries import QUERY_XRP_TRANSACTIONS, QUERY_RECENT_XRP_TRANSACTIONS
from ..base import BaseOperations
from typing import List, Dict, Any

class XRPQueryOperations(BaseOperations):
    def __init__(self, db):
        super().__init__(db)

    def query_xrp_transactions(self, block_number: int) -> List[Dict[str, Any]]:
        try:
            self.db.cursor.execute(QUERY_XRP_TRANSACTIONS, (
                block_number,
                ))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying XRP transactions for block {block_number}: {e}")
            return []
    
    def query_recent_xrp_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            self.db.cursor.execute(QUERY_RECENT_XRP_TRANSACTIONS, (
                limit,
                ))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying recent XRP transactions: {e}")
            return []

