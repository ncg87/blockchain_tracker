from ..base import BaseOperations
from typing import List, Dict, Any
from ...queries import QUERY_SOLANA_TRANSACTIONS, QUERY_RECENT_SOLANA_TRANSACTIONS

class SolanaQueryOperations(BaseOperations):
    def __init__(self, db):
        super().__init__(db)

    def query_transactions(self, block_number: int) -> List[Dict[str, Any]]:
        try:
            self.db.cursor.execute(QUERY_SOLANA_TRANSACTIONS, (
                block_number,
                ))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying Solana transactions for block {block_number}: {e}")
            return []
    
    def query_recent_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            self.db.cursor.execute(QUERY_RECENT_SOLANA_TRANSACTIONS, (
                limit,
            ))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying recent Solana transactions: {e}")
            return []
