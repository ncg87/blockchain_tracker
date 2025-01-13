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

class EthereumProcessor(EVMProcessor):
    """
    Ethereum processor class.
    """
    def __init__(self, sql_database, mongodb_database, querier):
        """
        Initialize the processor with a database instance.
        """
        super().__init__(sql_database, mongodb_database, 'Ethereum', querier)
        self.decoder = EthereumDecoder(sql_database)
    
    def process_logs(self, block_number, timestamp, batch_size=100, max_workers=4):
        """
        Process raw log data and store it.
        """
        block_number = decode_hex(block_number)
        timestamp = decode_hex(timestamp)
        
        try:
            # Get block logs
            logs = self.querier.get_block_logs(block_number)
            
            # Split logs into batches
            batches = [
                logs[i:i + batch_size] 
                for i in range(0, len(logs), batch_size)
            ]
            
            # Process batches in parallel
            decoder_logs = defaultdict(list)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                results = list(executor.map(self._process_logs_batch, batches))
            
            # Merge results
            for result in results:
                for tx_hash, decoded_logs in result.items():
                    decoder_logs[tx_hash].extend(decoded_logs)

            # Eventually going to insert into DB
            return self.mongodb_insert_ops.insert_ethereum_transactions(dict(decoder_logs), block_number, timestamp)
        
        except Exception as e:
            self.logger.error(f"Error processing logs for block {block_number}: {e}", exc_info=True)
    
    def _process_logs_batch(self, log_chunk):
        decoded_logs = defaultdict(list)
        for log in log_chunk:
            # Convert AttributeDict to dict
            log = dict(log)
            try:
                # Get transaction hash from log
                transaction_hash = normalize_hex(get_transaction_hash(log))
                
                # Get contract address from log and topics
                address = get_address(log)
                topics = log.get('topics', [])
                # If no address, skip log, possible that it is a contract creation
                if not address or not topics:
                    # self.database.insert_unknown_log(log) # maybe instead save the address
                    self.logger.debug(f"No address found for log: {log}")
                    decoded_log = {
                        "event": "Unknown",
                        "error": "Missing contract address or topics",
                        "raw_log": log
                    }
                    continue
                
                # ^^ checks to see if the logs is eligible for decoding
                abi = self.get_contract_abi(address)

                if abi is not None:
                    decoded_log = self.decoder.decode_log(log, abi)
                
                decoded_log['contract'] = address
                decoded_logs[transaction_hash].append(decoded_log)
                
            except Exception as e:
                error_log = {
                    "event": "DecodingError",
                    "error": str(e),
                    "raw_log": log
                }
                try:
                    tx_hash = log["transactionHash"].hex()
                    error_log["contract"] = log.get("address")
                    decoded_logs[tx_hash].append(error_log)
                except:
                    continue
        return decoded_logs
    
    def get_contract_abi(self, address):
        # First try to get ABI from DB
        
        result = self.sql_query_ops.query_ethereum_contract_abi(address)
        if result:
            return json.loads(result.get('abi'))
        # If not found, try to get it from Etherscan
        abi = self.querier.get_contract_abi(address)
        if abi:
            # If found, store it in DB
            self.sql_insert_ops.insert_ethereum_contract_abi(address, abi)
        return abi
    
    
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