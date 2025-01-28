from .bnb_processor import BNBProcessor
from .bnb_querier import BNBQuerier
from ..evm_models import EVMPipeline

class BNBPipeline(EVMPipeline):
    """
    BNB pipeline class supporting asynchronous block streaming.
    """
    def __init__(self, sql_database, mongodb_database):
        querier = BNBQuerier()
        processor = BNBProcessor(sql_database, mongodb_database, querier)
        super().__init__(sql_database, mongodb_database, 'bnb', querier, processor)