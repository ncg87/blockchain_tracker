import json

from ..base_models import BaseProcessor

class XRPProcessor(BaseProcessor):
    """
    XRP-specific processor.
    """
    def __init__(self, database, querier):
        super().__init__(database, 'XRP')
        self.querier = querier
        
    def process_block(self, ledger):
        """
        Process raw block data and store it in the database.
        """
        
        self.logger.info(f"Processing block {ledger['ledger_index']} on {self.network}")
        
        ledger = ledger['ledger']
        
        # Block specific data
        block_specific_data = {           
            "account_hash": ledger["account_hash"],
            "total_coins": ledger["total_coins"],
        } 
        
        # Prepare block data for insertion
        block_data = {
            "network": self.network,
            "block_number": ledger["ledger_index"],
            "block_hash": ledger["ledger_hash"],
            "parent_hash": ledger["parent_hash"],
            "timestamp": ledger["close_time"],
            "block_data": json.dumps(block_specific_data) # Process this to JSON upon Postgres insertion
        }
        
        # Insert block data into the database
        self.insert_ops.insert_block(block_data)
        self.logger.debug(f"Block {ledger['ledger_index']} stored successfully.")

        # Process transactions
        #self._process_transactions(block)
        