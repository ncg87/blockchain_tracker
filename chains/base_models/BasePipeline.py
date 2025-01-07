from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class BasePipeline(ABC):
    def __init__(self, database, chain_name):
        self.database = database
        self.chain_name = chain_name
        self.logger = logger
        
        self.logger.info(f"Starting {self.chain_name} pipeline...")

    @abstractmethod
    def run(self, *args, **kwargs):
        pass