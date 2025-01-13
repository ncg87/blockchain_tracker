from ..base_models import BaseProcessor
from ..utils import decode_hex, normalize_hex
from operator import itemgetter
from collections import defaultdict

# Common item getters
get_hash = itemgetter('hash')
get_from = itemgetter('from')
get_to = itemgetter('to')
get_value = itemgetter('value')
get_gas = itemgetter('gas')
get_gas_price = itemgetter('gasPrice')
get_chain_id = itemgetter('chainId')
get_parent_hash = itemgetter('parentHash')
get_block_number = itemgetter('number')
get_block_time = itemgetter('timestamp')

class EVMProcessor(BaseProcessor):
    """
    Abstract EVM processor class with common functionality.
    """
    def __init__(self, sql_database, mongodb_database, network_name: str, querier):
        super().__init__(sql_database, mongodb_database, network_name)
        self.querier = querier

    async def process_block(self, block):
        """
        Process raw block data and store it in the database.
        """
        block_number = decode_hex(get_block_number(block))
        timestamp = decode_hex(get_block_time(block))
        
        self.logger.info(f"Processing block {block_number} on {self.network}")
        
        # Insert block into MongoDB
        self.mongodb_insert_ops.insert_block(block, self.network, block_number, timestamp)

        # Insert block into PostgreSQL
        self.sql_insert_ops.insert_block(
            self.network, 
            block_number, 
            normalize_hex(get_hash(block)), 
            normalize_hex(get_parent_hash(block)), 
            timestamp
        )
        
        self.logger.debug(f"Processed {self.network} block {block_number}")
        
        # Process transactions
        self._process_transactions(block, block_number, timestamp)
    
    def _process_transactions(self, block, block_number, timestamp):
        """
        Process raw transaction data and store it.
        """
        try:
            self.logger.info(f"Processing {len(block['transactions'])} {self.network} transactions for block {block_number}")
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
            self.logger.debug(f"Processed {len(block['transactions'])} {self.network} transactions for block {block_number}")
        
        except Exception as e:
            self.logger.error(f"Error processing transactions for block {block_number}: {e}")
    
    def get_chain_id_with_default(self, tx):
        return decode_hex(get_chain_id(tx)) if 'chainId' in tx else 1
    
    def process_withdrawals(self, block):
        """
        Process raw withdrawal data and store it.
        """
        self.logger.info(f"Processing withdrawals for block {block['number']}")
        for withdrawl in block['withdrawals']:
            # Format withdrawal data
            withdrawal_data = {
                "network": self.network,
                "block_number": block["number"],
                "withdrawal_index": withdrawl["index"],
                "validator_index": withdrawl["validatorIndex"],
                "address": withdrawl["address"],
                "amount": withdrawl["amount"],
                "timestamp": block["timestamp"],
            }
            # Store withdrawal data
            self.database.insert_withdrawal(withdrawal_data)
            self.logger.debug(f"Withdrawal {withdrawal_data['withdrawal_index']} processed.")
