import json
from operator import itemgetter
from ..base_models import BaseProcessor
from .bitcoin_querier import BitcoinQuerier

# More optimal itemgetter functions
get_txid = itemgetter('txid')
get_version = itemgetter('version')
get_vout = itemgetter('vout')
get_value = itemgetter('value')

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
        block_number = block['height']
        timestamp = block['time']
        
        self.logger.info(f"Processing block {block_number} on {self.network}")
        
        # Insert block into MongoDB
        self.mongodb_insert_ops.insert_block(block, self.network, block_number, timestamp)
        
        # Prepare block data for SQL insertion
        block_data = {
            "network": self.network,
            "block_number": block_number,
            "block_hash": block["hash"],
            "parent_hash": block["previousblockhash"],
            "timestamp": timestamp,
        }
        # Insert block 
        self.sql_insert_ops.insert_block(block_data)
        self.logger.debug(f"Block {block_number} stored successfully.")
        
        # Process transactions
        self._process_transactions(block, block_number, timestamp)
    
    def _process_transactions(self, block, block_number, timestamp):
        """
        Process transactions in the block.
        """
        
            
        self.logger.info(f"Processing transactions in block {block_number} on {self.network}")
        try:
            for tx in block["tx"]:
                transaction = {
                    "block_number": block_number,
                    "transaction_id": get_txid(tx),
                    "version": get_version(tx),
                    "timestamp": timestamp,
                    "value_satoshis": sum(map(get_value, get_vout(tx))),
                }
                # Create a bulk insert operation
                self.sql_insert_ops.insert_bitcoin_transaction(transaction)
            self.logger.info(f"Inserted {len(block['tx'])} transactions in block {block_number} on {self.network}")
        except Exception as e:
            self.logger.error(f"Failed to process transactions in block {block_number}: {e}")
            return
