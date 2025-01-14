from ..evm_models.evm_processor import EVMProcessor
from operator import itemgetter
from ..utils import decode_hex
from ..base.base_decoder import BaseChainDecoder
get_chain_id = itemgetter('chainId')


class BaseChainProcessor(EVMProcessor):
    """
    Base-specific processor implementation.
    """
    def __init__(self, sql_database, mongodb_database, querier):
        super().__init__(
            sql_database=sql_database,
            mongodb_database=mongodb_database,
            network_name="Base",
            querier=querier,
            decoder=BaseChainDecoder(sql_database)
        )
    
    def get_chain_id_with_default(self, tx):
        return decode_hex(get_chain_id(tx)) if 'chainId' in tx else 8453
