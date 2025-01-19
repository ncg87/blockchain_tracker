from ..base import BaseOperations
from typing import List, Dict, Any
from ...queries import INSERT_BITCOIN_TRANSACTIONS
from psycopg2.extras import execute_values

class BitcoinInsertOperations(BaseOperations):
    def __init__(self, db):
        super().__init__(db)

    def insert_transactions(self, transactions: List[Dict[str, Any]], block_number: int) -> bool:
        """
        Bulk insert Bitcoin transactions into the PostgreSQL database.
        Table is partitioned by timestamp.
        """
        try:
            self.db.logger.info(f"Inserting Bitcoin transaction {block_number} into PostgreSQL database in bulk.")

            execute_values(self.db.cursor, INSERT_BITCOIN_TRANSACTIONS, transactions)
            self.db.conn.commit()
            
            self.db.logger.info(f"{len(transactions)} Bitcoin transactions inserted successfully in bulk.")
            return True
        except Exception as e:
            self.db.logger.error(f"Error inserting Bitcoin transactions: {e}")
            self.db.conn.rollback()
            return False
