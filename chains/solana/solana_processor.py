from ..base_models import BaseProcessor
import json
from operator import itemgetter


# Item getters
get_block_hash = itemgetter('blockhash')
get_previous_block_hash = itemgetter('previousBlockhash')
get_block_height = itemgetter('blockHeight')
get_block_time = itemgetter('blockTime')

class SolanaProcessor(BaseProcessor):
    """
    Solana processor class.
    """
    def __init__(self, sql_database, mongodb_database, querier):
        """
        Initialize the processor with a database instance.
        """
        super().__init__(sql_database, mongodb_database, 'Solana')
        self.querier = querier
    
    async def process_block(self, block):
        """
        Process raw block data and store it using the database class.
        """
        block_height = get_block_height(block)
        block_time = get_block_time(block)
        
        self.logger.info(f"Processing {self.network} block {block_height}")
        
        # Insert block into MongoDB
        self.mongodb_insert_ops.insert_block(block, self.network, block_height, block_time)
        
        # Prepare block data for SQL insertion
        block_data = {
            "network": self.network,
            "block_number": block_height,
            "block_hash": get_block_hash(block),
            "parent_hash": get_previous_block_hash(block),
            "timestamp": block_time,
        }
        self.sql_insert_ops.insert_block(block_data)
        self.logger.debug(f"Block {block_height} stored successfully.")
        
        # Process transactions
        #self._process_transactions(block)
    
    def _process_transactions(self, block):
        """
        Process raw transaction data, decode input data if ABI is available, and store it.
        """
        self.logger.info(f"Processing {self.network} transactions for block {block['blockHeight']}")
        for transaction in block['transactions']:
            
            transaction_data = {
                "network":  self.network,
                "block_number": transaction["blockHeight"],
                "timestamp": block["blockTime"],
                
                "transaction_hash": transaction["hash"],
                "from_address": transaction["from"],
                "to_address": transaction.get("to"),
                "amount": transaction.get("value"),
                "gas": transaction.get("gas"),
                "gas_price": transaction.get("gasPrice"),
                "input_data": transaction['input'].hex(),
            }
            
            self.database.insert_transaction(transaction_data)
            self.logger.debug(f"Transaction {transaction['signature']} stored successfully.")



