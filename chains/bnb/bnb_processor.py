import json
from hexbytes import HexBytes
from ..base_models import BaseProcessor
from ..utils import decode_hex, normalize_hex
from operator import itemgetter

# Item getters
get_hash = itemgetter('hash')
get_from = itemgetter('from')
get_to = itemgetter('to')
get_value = itemgetter('value')
get_gas = itemgetter('gas')
get_gas_price = itemgetter('gasPrice')
get_chain_id = itemgetter('chainId')
get_hash = itemgetter('hash')
get_parent_hash = itemgetter('parentHash')
get_block_number = itemgetter('number')
get_block_time = itemgetter('timestamp')

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
        
        height = decode_hex(get_block_number(block))
        timestamp = decode_hex(get_block_time(block))

        self.logger.info(f"Processing block {height} on {self.network}")
        
        # Insert block into MongoDB
        self.mongodb_insert_ops.insert_block(block, self.network, height, timestamp)
        
        # Prepare block data for SQL insertion
        block_data = {
            "network": self.network,
            "block_number": height,
            "block_hash": decode_hex(get_hash(block)),
            "parent_hash": decode_hex(get_parent_hash(block)),
            "timestamp": timestamp,
        }
        
        # Insert block, ***TODO: Add transaction processing*** 
        # ***TODO: Add withdrawals processing***
        # *** Make ASYNC ***
        
        self.sql_insert_ops.insert_block(block_data)
        self.logger.debug(f"{self.network} block {height} stored successfully.")
        
        # Process transactions
        self._process_transactions(block, height, timestamp)
        
        # Process withdrawals
        #self._process_withdrawals(block)
    
    def _process_transactions(self, block, block_number, timestamp):
        """
        Process raw transaction data, decode input data if ABI is available, and store it.
        """
        try:
            
            self.logger.info(f"Processing {self.network} transactions for block {decode_hex(block['number'])}")
            transactions = [
                (
                    block_number,
                    self.network,
                    normalize_hex(get_hash(transaction)),
                    self.get_chain_id_with_default(transaction),
                    get_from(transaction),
                    get_to(transaction),
                    decode_hex(get_value(transaction)),
                    decode_hex(get_gas(transaction)) * decode_hex(get_gas_price(transaction)),
                    timestamp
                ) for transaction in block['transactions']
            ]
            
            self.sql_insert_ops.insert_bulk_evm_transactions(self.network, transactions, block_number)
            self.logger.info(f"Processed {len(block['transactions'])} {self.network} transactions for block {block_number}")
            
            #for transaction in block['transactions']:
                
                # Checks if the transaction is between two wallets, and then check the logs for data about the transaction
                #if normalize_hex(transaction['input']) == '0x':
                #   self._process_native_transfer(transaction, timestamp)
            
                
                # Format transaction data
            #    transaction_data = {
            #        "block_number": block_number,
            #        "transaction_hash": normalize_hex(get_hash(transaction)),
            #        "chain_id" : self.get_chain_id_with_default(transaction),
            #        "from_address": get_from(transaction),
            #        "to_address": get_to(transaction),
            #        "amount": decode_hex(get_value(transaction)),
            #        "gas_costs": decode_hex(get_gas(transaction)) * decode_hex(get_gas_price(transaction)),
            #        "timestamp": timestamp
            #    }
                # Store transaction data
            #    self.sql_insert_ops.insert_evm_transaction(self.network, transaction_data)
            #    self.logger.debug(f"Transaction {normalize_hex(transaction['hash'])} processed.")
        
        except Exception as e:
            self.logger.error(f"Error processing transactions for block {block_number}: {e}")
    
    def get_chain_id_with_default(self, tx):
        return decode_hex(get_chain_id(tx)) if 'chainId' in tx else 1