from ..base_models import BaseProcessor
import json

class SolanaProcessor(BaseProcessor):
    """
    Solana processor class.
    """
    def __init__(self, database, querier):
        """
        Initialize the processor with a database instance.
        """
        super().__init__(database, 'Solana')
        self.querier = querier
    
    async def process_block(self, block):
        """
        Process raw block data and store it using the database class.
        """
    
        
        self.logger.info(f"Processing {self.network} block {block['blockHeight']}")
        
        block_specific_data = {
            "parent_slot": block["parentSlot"],
        }
        
        block_data = {
            "network": self.network,
            "block_number": block["blockHeight"],
            "block_hash": block["blockhash"],
            "parent_hash": block["previousBlockhash"],
            "timestamp": block["blockTime"],
            "block_data": json.dumps(block_specific_data)
        }
        self.insert_ops.insert_block(block_data)
        self.logger.debug(f"Block {block['blockHeight']} stored successfully.")
        
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



