from ..evm_models import EVMPipeline
from .ethereum_processor import EthereumProcessor
from .ethereum_querier import EthereumQuerier

class EthereumPipeline(EVMPipeline):
    """
    Ethereum pipeline class supporting asynchronous block streaming.
    """
    def __init__(self, sql_database, mongodb_database):
        # Initialize querier and processor
        querier = EthereumQuerier()
        processor = EthereumProcessor(sql_database, mongodb_database, querier)
        # Initialize pipeline
        super().__init__(sql_database, mongodb_database, 'Ethereum', querier, processor)