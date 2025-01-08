import json
from hexbytes import HexBytes
from ..base_models import BaseProcessor
from ..utils import decode_hex, normalize_hex

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
        
    async def process_block(self, block):
        """
        Process raw block data and store it in the database.
        """
        self.logger.info(f"Processing block {block['number']} on {self.network}")
        
        # Block specific data
        block_specific_data = {           
            "miner": block["miner"],
            "gas_limit": decode_hex(block["gasLimit"]),
            "gas_used": decode_hex(block["gasUsed"]),
            "base_fee": decode_hex(block["baseFeePerGas"]),
            "block_size": decode_hex(block["size"]),
            "proof_of_authority_data": normalize_hex(block["proofOfAuthorityData"] if "proofOfAuthorityData" in block else block["extraData"]),
            "blob_gas_used": decode_hex(block["blobGasUsed"]),
            "excess_blob_gas": decode_hex(block["excessBlobGas"]),
        } 
        # Prepare block data for insertion
        block_data = {
            "network": self.network,
            "block_number": decode_hex(block["number"]),
            "block_hash": normalize_hex(block["hash"]),
            "parent_hash": normalize_hex(block["parentHash"]),
            "timestamp": decode_hex(block["timestamp"]),
            "block_data": json.dumps(block_specific_data) # Process this to JSON upon Postgres insertion
        }
        
        # Insert block, ***TODO: Add transaction processing*** 
        # ***TODO: Add withdrawals processing***
        # *** Make ASYNC ***
        
        self.insert_ops.insert_block(block_data)
        self.logger.debug(f"Block {block['number']} stored successfully.")
        
        # Process transactions
        #self._process_transactions(block)
        
        # Process withdrawals
        #self._process_withdrawals(block)
        