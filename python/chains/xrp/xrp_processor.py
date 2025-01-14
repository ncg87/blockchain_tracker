import json
from ..base_models import BaseProcessor
from operator import itemgetter

get_ledger = itemgetter('ledger')
get_ledger_hash = itemgetter('ledger_hash')
get_ledger_index = itemgetter('ledger_index')
get_block_time = itemgetter('close_time')
get_parent_hash = itemgetter('parent_hash')

get_hash = itemgetter('hash')
get_account = itemgetter('Account')
get_type = itemgetter('TransactionType')
get_fee = itemgetter('Fee')



class XRPProcessor(BaseProcessor):
    """
    XRP-specific processor.
    """
    def __init__(self, sql_database, mongodb_database, querier):
        super().__init__(sql_database, mongodb_database, 'XRP')
        self.querier = querier
        
    async def process_block(self, ledger):
        """
        Process raw block data and store it in the database.
        """
        
        ledger_index = get_ledger_index(ledger)
        
        self.logger.info(f"Processing block {ledger_index} on {self.network}")
        
        
        ledger = get_ledger(ledger)
        timestamp = get_block_time(ledger) + 946684800
        # Insert block into MongoDB, add 30 years since XRP has its own epoch
        self.mongodb_insert_ops.insert_block(ledger, self.network, ledger_index, timestamp)
        
        # Insert block data into the PostgreSQL database
        self.sql_insert_ops.insert_block(self.network, ledger_index, get_ledger_hash(ledger), get_parent_hash(ledger), timestamp)
        self.logger.debug(f"Processed {self.network} block {ledger_index}")

        # Process transactions
        self._process_transactions(ledger, ledger_index, timestamp)
        
    def _process_transactions(self, ledger, ledger_index, timestamp):
        """
        Process transactions in the ledger.
        """
        try:
            self.logger.info(f"Processing {len(ledger['transactions'])} {self.network} transactions for block {ledger_index}")
            transactions = [
                (
                    ledger_index,
                    get_hash(tx),
                    get_account(tx),
                    get_type(tx),
                    get_fee(tx),
                    timestamp,
                ) for tx in ledger['transactions']
            ]
            
            self.sql_insert_ops.insert_bulk_xrp_transactions(transactions, ledger_index)
            self.logger.debug(f"Processed {len(ledger['transactions'])} {self.network} transactions for block {ledger_index}")
        except Exception as e:
            self.logger.error(f"Error processing transactions for block {ledger_index}: {e}")
            
        