from ..base import BaseOperations
from typing import List, Dict, Any
from ...queries import QUERY_BITCOIN_TRANSACTIONS, QUERY_RECENT_BITCOIN_TRANSACTIONS
class BitcoinQueryOperations(BaseOperations):
    def __init__(self, db):
        super().__init__(db)

    def query_transactions(self, block_number: int) -> List[Dict[str, Any]]:
        """
        Query Bitcoin transactions for a specific block.
        """
        try:
            self.db.cursor.execute(QUERY_BITCOIN_TRANSACTIONS, (
                block_number,
            ))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying Bitcoin transactions for block {block_number}: {e}")
            return []
    
    def query_recent_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Query recent Bitcoin transactions.
        """
        try:
            self.db.cursor.execute(QUERY_RECENT_BITCOIN_TRANSACTIONS, (
                limit,
            ))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying recent Bitcoin transactions: {e}")
            return []