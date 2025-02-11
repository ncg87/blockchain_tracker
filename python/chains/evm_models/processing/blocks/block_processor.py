from operator import itemgetter
from database import DatabaseOperator
import logging
from concurrent.futures import ThreadPoolExecutor
from ....utils import decode_hex, normalize_hex
from ...utils import CHAIN_IDS


# Block item getters
get_hash = itemgetter('hash')
get_block_number = itemgetter('number')
get_parent_hash = itemgetter('parentHash')
get_timestamp = itemgetter('timestamp')

# EVM Transaction item getters
get_from = itemgetter('from')
get_to = itemgetter('to')
get_value = itemgetter('value')
get_gas = itemgetter('gas')
get_gas_price = itemgetter('gasPrice')
get_chain_id = itemgetter('chainId')


class BlockProcessor:

    def __init__(self, db_operator: DatabaseOperator, chain: str):
        self.chain = chain  # Normalize chain name
        self.db_operator = db_operator
        self.logger = logging.getLogger(__name__)
        self.batch_size = 1000
        self.chain_id = CHAIN_IDS.get(self.chain)
        if self.chain_id is None:
            self.logger.warning(f"No default chain ID found for {self.chain}")
        self._transaction_executor = ThreadPoolExecutor(max_workers=8)
        self._processing_tasks = set()

    def process(self, block: dict):
        """
        Process block and schedule transaction processing asynchronously.
        Returns block_number and timestamp immediately.
        """
        try:
            block_number = decode_hex(get_block_number(block))
            timestamp = decode_hex(get_timestamp(block))
            
            self.logger.info(f"Processing block {block_number} on {self.chain}")
            
            # Insert block data
            self.db_operator.mongodb.insert.insert_block(block, self.chain, block_number, timestamp)
            
            # Insert block timestamp using tuple format
            self.db_operator.clickhouse.insert.block_timestamp(
                self.chain,
                timestamp,
                block_number
            )
            
            block_hash = normalize_hex(get_hash(block))
            parent_hash = normalize_hex(get_parent_hash(block))

            self.db_operator.sql.insert.block.insert_block(
                self.chain,
                block_number,
                block_hash,
                parent_hash,
                timestamp
            )
            
            # Schedule transaction processing in background
            self._transaction_executor.submit(
                self.process_transactions,
                block,
                block_number,
                timestamp
            )
            
            return block_number, timestamp
            
        except Exception as e:
            self.logger.error(f"Error processing block {block_number} for {self.chain}: {e}")
            raise e
    
    # Process the transactions
    def process_transactions(self, block: dict, block_number: int, timestamp: int):
        try:
            transactions = block.get('transactions', [])
            if not transactions:
                return
            self.logger.info(f"Processing {len(transactions)} transactions on {self.chain} for block {block_number}")
            # Pre-process transactions into batches
            transaction_batches = [
                transactions[i:i + self.batch_size] 
                for i in range(0, len(transactions), self.batch_size)
            ]
            
            # Process batches in parallel
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = []
                for batch in transaction_batches:
                    futures.append(
                        executor.submit(
                            self._process_transaction_batch,
                            batch,
                            block_number,
                            timestamp
                        )
                    )
                    
                    # Collect all processed transactions
                all_transactions = []
                for future in futures:
                    try:
                        batch_result = future.result()
                        all_transactions.extend(batch_result)
                    except Exception as e:
                        self.logger.error(f"Error processing transaction batch: {e}")
            
            # Bulk insert all transactions
            if all_transactions:
                self.db_operator.sql.insert.evm.transactions(
                    self.chain, 
                    all_transactions, 
                    block_number
                )
        except Exception as e:
            self.logger.error(f"Error processing transactions for block {block_number}: {e}")

    def _process_transaction_batch(self, transaction_batch, block_number, timestamp):
        """
        Process a batch of transactions.
        """
        try:
            processed_transactions = []
            # Process each transaction in the batch into a tuple
            for transaction in transaction_batch:
                processed_tx = (
                    block_number,
                    self.chain,
                    normalize_hex(get_hash(transaction)),
                    self.get_chain_id_with_default(transaction),
                    get_from(transaction),
                    get_to(transaction),
                    decode_hex(get_value(transaction)),
                    decode_hex(get_gas(transaction)) * decode_hex(get_gas_price(transaction)),
                    timestamp
                )
                processed_transactions.append(processed_tx)
        except Exception as e:
            self.logger.error(f"Error processing transaction batch: {e}")
            return []
        return processed_transactions
    
    def get_chain_id_with_default(self, transaction):
        """
        Get the chain ID from the transaction or use the default chain ID.
        If neither is available, return None.
        """
        return get_chain_id(transaction) if 'chainId' in transaction else self.chain_id
    
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

