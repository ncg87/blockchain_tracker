import json

from ..base_models import BaseProcessor

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
        
        self.logger.info(f"Processing block {ledger['ledger_index']} on {self.network}")
        
        ledger = ledger['ledger']
        
        # Insert block into MongoDB
        self.mongodb_insert_ops.insert_block(ledger, self.network, ledger['ledger_index'], ledger['close_time'])
        
        
        # Prepare block data for insertion
        block_data = {
            "network": self.network,
            "block_number": ledger["ledger_index"],
            "block_hash": ledger["ledger_hash"],
            "parent_hash": ledger["parent_hash"],
            "timestamp": ledger["close_time"],
        }
        
        # Insert block data into the database
        self.sql_insert_ops.insert_block(block_data)
        self.logger.debug(f"Block {ledger['ledger_index']} stored successfully.")

        # Process transactions
        #self._process_transactions(block)
        
        def _process_transactions(self, ledger):
            """
            Process transactions in the ledger.
            """
            pass
        