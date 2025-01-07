import json

from ..base_models import BaseProcessor

class BNBProcessor(BaseProcessor):
    """
    BNB processor class.
    """
    def __init__(self, database, querier):
        """
        Initialize the BNB processor with a database and querier.
        """
        super().__init__(database, 'BNB')
        self.querier = querier
        
    def process_block(self, block):
        """
        Process raw block data and store it in the database.
        """
        self.logger.info(f"Processing block {block['number']} on {self.network}")
        
        # Block specific data
        block_specific_data = {           
            "miner": block["miner"],
            "gas_limit": block["gasLimit"],
            "gas_used": block["gasUsed"],
            "base_fee": block["baseFeePerGas"],
            "block_size": block["size"],
            "proof_of_authority_data": block["proofOfAuthorityData"].hex(),
            "blob_gas_used": block["blobGasUsed"],
            "excess_blob_gas": block["excessBlobGas"],
        } 
        # Prepare block data for insertion
        block_data = {
            "network": self.network,
            "block_number": block["number"],
            "block_hash": block["hash"].hex(),
            "parent_hash": block["parentHash"].hex(),
            "timestamp": block["timestamp"],
            "block_data": json.dumps(block_specific_data) # Process this to JSON upon Postgres insertion
        }
        # Insert block 
        self.insert_ops.insert_block(block_data)
        self.logger.debug(f"Block {block['number']} stored successfully.")
        
        # Process transactions
        #self._process_transactions(block)
        
        # Process withdrawals
        #self._process_withdrawals(block)