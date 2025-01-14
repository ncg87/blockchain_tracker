from ..evm_models import EVMProcessor
from operator import itemgetter
from ..utils import decode_hex
from ..bnb.bnb_decoder import BNBDecoder

# Item getters 
get_chain_id = itemgetter('chainId')

class BNBProcessor(EVMProcessor):
    """
    BNB processor class.
    """
    def __init__(self, sql_database, mongodb_database, querier):
        """
        Initialize the BNB processor with a database and querier.
        """
        super().__init__(sql_database, mongodb_database, 'BNB', querier, BNBDecoder(sql_database))  
        
    
    def get_chain_id_with_default(self, tx):
        return decode_hex(get_chain_id(tx)) if 'chainId' in tx else 56
