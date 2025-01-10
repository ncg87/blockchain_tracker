import json
from ..base_models import BaseProcessor
from operator import itemgetter

get_ledger = itemgetter('ledger')
get_ledger_hash = itemgetter('ledger_hash')
get_ledger_index = itemgetter('ledger_index')
get_block_time = itemgetter('close_time')
get_parent_hash = itemgetter('parent_hash')


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
        
        
        # Prepare block data for insertion
        block_data = {
            "network": self.network,
            "block_number": ledger_index,
            "block_hash": get_ledger_hash(ledger),
            "parent_hash": get_parent_hash(ledger),
            "timestamp": timestamp,
        }
        
        # Insert block data into the database
        self.sql_insert_ops.insert_block(block_data)
        self.logger.debug(f"Block {ledger_index} stored successfully.")

        # Process transactions
        #self._process_transactions(block)
        
        def _process_transactions(self, ledger):
            """
            Process transactions in the ledger.
            """
            pass
        