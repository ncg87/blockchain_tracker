import json

from ..base_models import BaseProcessor
from .bitcoin_querier import BitcoinQuerier

class BitcoinProcessor(BaseProcessor):
    """
    Bitcoin processor class.
    """
    def __init__(self, database, querier):
        super().__init__(database, 'Bitcoin')
        self.querier = querier
        
    async def process_block(self, block):
        """
        Process raw block data and store it in the database.
        """
        self.logger.info(f"Processing block {block['height']} on {self.network}")
        
        # Block specific data
        block_specific_data = {           
            "version": block["version"],
            "merkle_root": block["merkleroot"],
            "chainwork": block["chainwork"],
            "bits": block["bits"],
            "weight": block["weight"],
            "size": block["size"],
            "num_tx": block["nTx"],
        } 
        # Prepare block data for insertion
        block_data = {
            "network": self.network,
            "block_number": block["height"],
            "block_hash": block["hash"],
            "parent_hash": block["previousblockhash"],
            "timestamp": block["time"],
            "block_data": json.dumps(block_specific_data) # Process this to JSON upon Postgres insertion
        }
        # Insert block 
        self.insert_ops.insert_block(block_data)
        self.logger.debug(f"Block {block['height']} stored successfully.")
        
        # Process transactions
        #self._process_transactions(block)
    
    def _process_transactions(self, block):
        """
        Process transactions in the block.
        """
        try:
            for tx in block["tx"]:
                pass
        except Exception as e:
            self.logger.error(f"Failed to process transactions in block {block['height']}: {e}")
            return
