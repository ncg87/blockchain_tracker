import json

from ..base_models import BaseProcessor
from .bitcoin_querier import BitcoinQuerier

class BitcoinProcessor(BaseProcessor):
    """
    Bitcoin processor class.
    """
    def __init__(self, sql_database, mongodb_database, querier):
        super().__init__(sql_database, mongodb_database, 'Bitcoin')
        self.querier = querier
        
    async def process_block(self, block):
        """
        Process raw block data and store it in the database.
        """
        self.logger.info(f"Processing block {block['height']} on {self.network}")
        
        # Insert block into MongoDB
        self.mongodb_insert_ops.insert_block(block, self.network, block['height'])
        
        # Prepare block data for SQL insertion
        block_data = {
            "network": self.network,
            "block_number": block["height"],
            "block_hash": block["hash"],
            "parent_hash": block["previousblockhash"],
            "timestamp": block["time"],
        }
        # Insert block 
        self.sql_insert_ops.insert_block(block_data)
        self.logger.debug(f"Block {block['height']} stored successfully.")
        
        # Process transactions
        #self._process_transactions(block)
    
    def _process_transactions(self, block):
        """
        Process transactions in the block.
        """
        try:
            for tx in block["tx"]:
                transaction = {
                    "block_number": block["height"],
                    "timestamp": block["time"],
                    "hash": tx["hash"],
                    "id": tx["txid"],
                    "amount": tx["vout"][0]["value"],
                    "fee": tx["fee"],
                }
                self.insert_ops.insert_transaction(transaction)
        except Exception as e:
            self.logger.error(f"Failed to process transactions in block {block['height']}: {e}")
            return
