from ..utils import decode_hex, normalize_hex
from operator import itemgetter
from ..arbitrum.arbitrum_decoder import ArbitrumDecoder
from ..evm_models import EVMProcessor

# Item getters
get_logs = itemgetter('logs')
get_address = itemgetter('address')
get_topics = itemgetter('topics')
get_transaction_hash = itemgetter('transactionHash')
get_chain_id = itemgetter('chainId')

class ArbitrumProcessor(EVMProcessor):
    """
    Arbitrum processor class.
    """
    def __init__(self, sql_database, mongodb_database, querier):
        """
        Initialize the processor with a database instance.
        """
        super().__init__(
            sql_database=sql_database,
            mongodb_database=mongodb_database,
            network_name="Arbitrum",
            querier=querier,
            decoder=ArbitrumDecoder(sql_database)
        )
    
    def get_chain_id_with_default(self, tx):
        return decode_hex(get_chain_id(tx)) if 'chainId' in tx else 42161
    