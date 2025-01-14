import json
from ..utils import decode_hex, normalize_hex
from operator import itemgetter
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from ..ethereum.ethereum_decoder import EthereumDecoder
from ..evm_models import EVMProcessor

# Item getters
get_logs = itemgetter('logs')
get_address = itemgetter('address')
get_topics = itemgetter('topics')
get_transaction_hash = itemgetter('transactionHash')
get_chain_id = itemgetter('chainId')
class EthereumProcessor(EVMProcessor):
    """
    Ethereum processor class.
    """
    def __init__(self, sql_database, mongodb_database, querier):
        """
        Initialize the processor with a database instance.
        """
        super().__init__(sql_database, mongodb_database, 'Ethereum', querier, EthereumDecoder(sql_database))
        
    
    def get_chain_id_with_default(self, tx):
        return decode_hex(get_chain_id(tx)) if 'chainId' in tx else 1
    
    def _process_native_transfer(self, transaction, timestamp):
        """
        Process native transfer transaction data.
        """
        transaction_data = {
                "block_number": transaction["blockNumber"],
                "transaction_hash": normalize_hex(transaction["hash"]),
                "from_address": transaction["from"],
                "to_address": transaction.get("to"),
                "amount": decode_hex(transaction.get("value")),
                "gas": decode_hex(transaction.get("gas")),
                "gas_price": decode_hex(transaction.get("gasPrice")),
                "timestamp": timestamp,
            }
        
        self.sql_insert_ops.insert_evm_transaction(self.network, transaction_data)
        self.logger.debug(f"Transaction {normalize_hex(transaction['hash'])} processed.")