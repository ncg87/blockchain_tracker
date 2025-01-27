from ..base_models import BaseProcessor
import json
from operator import itemgetter
import numpy as np


# Item getters
get_block_hash = itemgetter('blockhash')
get_previous_block_hash = itemgetter('previousBlockhash')
get_block_height = itemgetter('blockHeight')
get_block_time = itemgetter('blockTime')
get_transactions = itemgetter('transactions')
get_transaction = itemgetter('transaction')
get_signature = itemgetter('signatures')
get_meta = itemgetter('meta')
get_fee = itemgetter('fee')
get_pre_token_balances = itemgetter('preBalances')
get_post_token_balances = itemgetter('postBalances')
get_account_keys = itemgetter('accountKeys')
get_pubkey = itemgetter('pubkey')
get_message = itemgetter('message')

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
        try:
            block_height = get_block_height(block)
            block_time = get_block_time(block)
                
            self.logger.info(f"Processing {self.network} block {block_height}")
            
            # Insert block into MongoDB
            self.mongodb_operator.insert.block.insert_block(block, self.network, block_height, block_time)
            
            # Insert block into PostgreSQL
            self.sql_operator.insert.block.insert_block(self.network, block_height, get_block_hash(block), get_previous_block_hash(block), block_time)
            self.logger.debug(f"{self.network} block {block_height} stored successfully.")
            
            # Process transactions
            self._process_transactions(block, block_height, block_time)
            
            self.logger.debug(f"Processed {self.network} block {block_height}")
        except Exception as e:
            self.logger.error(f"Error processing block {block_height}: {e}")
    
    def _process_transactions(self, block, block_height, timestamp):
        """
        Process raw transaction data, decode input data if ABI is available, and store it.
        """
        try:
            transactions = get_transactions(block)
            self.logger.info(f"Processing {len(transactions)} {self.network} transactions for block {block_height}")
            transacations_data = []
            for tx in transactions:
                meta = get_meta(tx)
                transaction = get_transaction(tx)
                transacations_data.append(
                    (
                        block_height,
                        get_signature(transaction)[0],
                        self._get_transaction_value(meta),
                        get_fee(meta),
                        get_pubkey(get_account_keys(get_message(transaction))[0]),
                        timestamp,
                    )
                )
            
            self.sql_operator.insert.solana.insert_transactions(transacations_data, block_height)
            self.logger.debug(f"Processed {len(transactions)} {self.network} transactions for block {block_height}")
        except Exception as e:
            self.logger.error(f"Error processing transactions for block {block_height}: {e}")

    def _get_transaction_value(self, meta):
        """
        Get the transaction value from the transaction data.
        """
        pre_balances = get_pre_token_balances(meta)
        post_balances = get_post_token_balances(meta)
        fee = get_fee(meta)
        
        return int(np.subtract(np.sum(np.abs(np.subtract(post_balances, pre_balances))), fee))


