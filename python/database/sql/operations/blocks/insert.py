from ..base import BaseOperations
from ...queries.blocks.insert import INSERT_BLOCK

class BlockInsertOperations(BaseOperations):
    def __init__(self, db):
        super().__init__(db)

    def insert_block(self, chain, block_number, block_hash, parent_hash, timestamp) -> bool:
        """
        Insert a block into the PostgreSQL database.
        The table is partitioned by chain, so chain must be provided.
        """
        try:
            self.db.logger.info(f"Inserting {chain} block {block_number} into PostgreSQL database...")
            
            self.db.cursor.execute(INSERT_BLOCK, (chain, block_number, block_hash, parent_hash, timestamp))
            self.db.conn.commit()
            
            self.db.logger.info(f"{chain} block {block_number} inserted successfully into PostgreSQL database...")
            return True
        except Exception as e:
            self.db.logger.error(f"Error inserting {chain} block {block_number} into PostgreSQL database: {e}")
            self.db.conn.rollback()
            return False