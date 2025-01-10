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
        self.logger.info(f"Processing block {decode_hex(block['number'])} on {self.network}")
        
        # Insert block into MongoDB
        self.mongodb_insert_ops.insert_block(block, self.network, decode_hex(block['number']), decode_hex(block['timestamp']))
        
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
        self._process_transactions(block)
        
        # Process withdrawals
        #self._process_withdrawals(block)
    
    def _process_transactions(self, block):
        """
        Process raw transaction data, decode input data if ABI is available, and store it.
        """
        try:
            self.logger.info(f"Processing {self.network} transactions for block {decode_hex(block['number'])}")
            for transaction in block['transactions']:
                timestamp = decode_hex(block['timestamp'])
                
                # Checks if the transaction is between two wallets, and then check the logs for data about the transaction
                #if normalize_hex(transaction['input']) == '0x':
                #   self._process_native_transfer(transaction, timestamp)
                
                # Format transaction data
                transaction_data = {
                    "block_number": decode_hex(transaction["blockNumber"]),
                    "transaction_hash": normalize_hex(transaction["hash"]),
                    "chain_id" : decode_hex(transaction.get("chainId",1)),
                    "from_address": transaction["from"],
                    "to_address": transaction.get("to"),
                    "amount": decode_hex(transaction.get("value")),
                    "gas_costs": self.calculate_gas_cost(transaction),
                    "timestamp": timestamp
                }
                # Store transaction data
                self.sql_insert_ops.insert_evm_transaction(self.network, transaction_data)
                self.logger.debug(f"Transaction {normalize_hex(transaction['hash'])} processed.")
            self.logger.info(f"Processed {len(block['transactions'])} {self.network} transactions for block {decode_hex(block['number'])}")
        
        except Exception as e:
            self.logger.error(f"Error processing transactions for block {decode_hex(block['number'])}: {e}")
    
    def calculate_gas_cost(self, transaction):
        """
        Calculate the gas cost of a Ethereum transaction.
        """
        try:
            return decode_hex(transaction.get("gas")) * decode_hex(transaction.get("gasPrice"))
        except Exception as e:
            self.logger.error(f"Error calculating gas cost for transaction {normalize_hex(transaction['hash'])}: {e}")
            return None
