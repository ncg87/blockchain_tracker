from ..base_models import BasePipeline
from .bitcoin_processor import BitcoinProcessor
from .bitcoin_querier import BitcoinQuerier
import logging

class BitcoinPipeline(BasePipeline):
    """
    Bitcoin pipeline class.
    """
    def __init__(self, database):
        super().__init__(database, 'Bitcoin')
        
        self.querier = BitcoinQuerier()
        self.processor = BitcoinProcessor(self.database, self.querier)

    def run(self, start_block=None, end_block=None):
        self.logger.info("Starting Bitcoin pipeline...")
