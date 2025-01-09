import json
from hexbytes import HexBytes
from ..base_models import BaseProcessor
from ..utils import decode_hex, normalize_hex

class BNBProcessor(BaseProcessor):
    """
    BNB processor class.
    """
    def __init__(self, sql_database, mongodb_database, querier):
        """
        Initialize the BNB processor with a database and querier.
        """
        super().__init__(sql_database, mongodb_database, 'BNB')
        self.querier = querier
        
    async def process_block(self, block):
        """
        Process raw block data and store it in the database.
        """
        self.logger.info(f"Processing block {block['number']} on {self.network}")
        
        # Insert block into MongoDB
        self.mongodb_insert_ops.insert_block(block, self.network, block['number'], block['timestamp'])
        
        # Prepare block data for SQL insertion
        block_data = {
            "network": self.network,
            "block_number": decode_hex(block["number"]),
            "block_hash": normalize_hex(block["hash"]),
            "parent_hash": normalize_hex(block["parentHash"]),
            "timestamp": decode_hex(block["timestamp"]),
        }
        
        # Insert block, ***TODO: Add transaction processing*** 
        # ***TODO: Add withdrawals processing***
        # *** Make ASYNC ***
        
        self.sql_insert_ops.insert_block(block_data)
        self.logger.debug(f"Block {block['number']} stored successfully.")
        
        # Process transactions
        #self._process_transactions(block)
        
        # Process withdrawals
        #self._process_withdrawals(block)
        