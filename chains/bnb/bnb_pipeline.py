from ..base_models import BasePipeline
from .bnb_querier import BNBQuerier
from .bnb_processor import BNBProcessor

class BNBPipeline(BasePipeline):
    """
    BNB pipeline class.
    """
    def __init__(self, database):
        super().__init__(database, 'BNB')
        self.querier = BNBQuerier()
        self.processor = BNBProcessor(database, self.querier)