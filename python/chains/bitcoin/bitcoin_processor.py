import json
from operator import itemgetter
from ..base_models import BaseProcessor
from .bitcoin_querier import BitcoinQuerier

# More optimal itemgetter functions
get_txid = itemgetter('txid')
get_version = itemgetter('version')
get_vout = itemgetter('vout')
get_value = itemgetter('value')
get_fee = itemgetter('fee')
get_parent_hash = itemgetter('previousblockhash')
get_hash = itemgetter('hash')

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
        
        # Insert block into PostgreSQL
        self.sql_insert_ops.insert_block(self.network, block_number, get_hash(block), get_parent_hash(block), timestamp)
        self.logger.debug(f"Processed {self.network} block {block_number}")
        
        # Process transactions
        self._process_transactions(block, block_number, timestamp)
    
    def _process_transactions(self, block, block_number, timestamp):
        """
        Process transactions in the block.
        """
         
        self.logger.info(f"Processing transactions in block {block_number} on {self.network}")
        try: 
            transactions = [
                (
                    block_number,
                    get_txid(tx),
                    get_version(tx),
                    sum(map(get_value, get_vout(tx))),
                    timestamp,
                    self.get_fee_with_default(tx),
                ) for tx in block["tx"]
            ]
            
            self.sql_insert_ops.insert_bulk_bitcoin_transactions(transactions, block_number)
            self.logger.debug(f"Inserted {len(block['tx'])} transactions in block {block_number} on {self.network}")
        except Exception as e:
            self.logger.error(f"Failed to process transactions in block {block_number}: {e}")
            return
        
    def get_fee_with_default(self, tx):
        return get_fee(tx) if 'fee' in tx else 0
