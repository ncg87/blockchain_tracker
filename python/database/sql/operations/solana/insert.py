from ..base import BaseOperations
from typing import List, Dict, Any
from ...queries import INSERT_SOLANA_TRANSACTIONS
from psycopg2.extras import execute_values

class SolanaInsertOperations(BaseOperations):
    def __init__(self, db):
        super().__init__(db)

    def insert_transactions(self, transactions: List[Dict[str, Any]], block_number: int) -> bool:
        """
        Bulk insert Solana transactions into the PostgreSQL database.
        Table is partitioned by timestamp.
        """
        try:
            self.db.logger.info(f"Inserting Solana {block_number} transaction into PostgreSQL database in bulk.")
            
            execute_values(
                self.db.cursor, 
                INSERT_SOLANA_TRANSACTIONS, 
                transactions, 
                page_size=1000
            )
            self.db.conn.commit()
            self.db.logger.info(f"{len(transactions)} Solana transactions inserted successfully in bulk.")
            return True
        except Exception as e:
            self.db.logger.error(f"Error inserting Solana transaction: {e}")
            self.db.conn.rollback()
            return False