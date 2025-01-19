from ...queries import INSERT_XRP_TRANSACTIONS
from ..base import BaseOperations
from typing import List, Dict, Any
from psycopg2.extras import execute_values

class XRPInsertOperations(BaseOperations):
    def __init__(self, db):
        super().__init__(db)
    
    def insert_transactions(self, transactions: List[Dict[str, Any]], block_number: int) -> bool:
        """
        Bulk insert XRP transactions into the PostgreSQL database.
        Table is partitioned by timestamp.
        """
        try:
            self.db.logger.info(f"Inserting XRP transaction {block_number} into PostgreSQL database in bulk.")
            
            execute_values(self.db.cursor, 
                           INSERT_XRP_TRANSACTIONS, 
                           transactions, 
                           page_size=1000
                           )
            self.db.conn.commit()
            
            self.db.logger.info(f"{len(transactions)} XRP transactions inserted successfully in bulk.")
            return True
        except Exception as e:
            self.db.logger.error(f"Error inserting XRP transactions: {e}")
            self.db.conn.rollback()
            return False
