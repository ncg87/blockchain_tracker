from ..base_models import BasePipeline
from .solana_querier import SolanaQuerier
from .solana_processor import SolanaProcessor
import logging

class SolanaPipeline(BasePipeline):
    """
    Solana pipeline class.
    """
    def __init__(self, database):
        super().__init__(database, 'Solana')
        self.querier = SolanaQuerier()
        self.processor = SolanaProcessor(database, self.querier)