from ..base_models import BasePipeline
from .xrp_querier import XRPQuerier
from .xrp_processor import XRPProcessor

class XRPPipeline(BasePipeline):
    """
    XRP-specific pipeline.
    """
    def __init__(self, database):
        super().__init__(database, 'XRP')
        self.querier = XRPQuerier()
        self.processor = XRPProcessor(self.database, self.querier)
    # TODO: Add a method to get the latest block number and process, should it be async?
    
