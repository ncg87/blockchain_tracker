from ..base_models import BaseProcessor
from ..utils import decode_hex, normalize_hex
from operator import itemgetter
from abc import abstractmethod
from operator import itemgetter
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import json
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
get_logs = itemgetter('logs')
get_address = itemgetter('address')
get_topics = itemgetter('topics')
get_transaction_hash = itemgetter('transactionHash')

class EVMProcessor(BaseProcessor):
    """
    Abstract EVM processor class with common functionality.
    """
    def __init__(self, sql_database, mongodb_database, network_name: str, querier, decoder):
        super().__init__(sql_database, mongodb_database, network_name)
        self.querier = querier
        self.decoder = decoder

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
    
    @ abstractmethod
    def get_chain_id_with_default(self, tx):
        pass
    
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
            self.mongodb_insert_ops.insert_evm_transactions(dict(decoder_logs), self.network, block_number, timestamp)
        
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
        
        result = self.sql_query_ops.query_evm_contract_abi(self.network, address)
        if result:
            return json.loads(result.get('abi'))
        # If not found, try to get it from Etherscan
        abi = self.querier.get_contract_abi(address)
        if abi:
            # If found, store it in DB
            self.sql_insert_ops.insert_evm_contract_abi(self.network, address, abi)
        return abi
    
    
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
