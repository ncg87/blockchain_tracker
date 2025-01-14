from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class BasePipeline(ABC):
    def __init__(self, sql_database, mongodb_database, chain_name):
        self.sql_database = sql_database
        self.mongodb_database = mongodb_database
        self.chain_name = chain_name
        self.logger = logger
        
        self.logger.info(f"Starting {self.chain_name} pipeline...")

    @abstractmethod
    async def run(self, *args, **kwargs):
        pass
    
    @abstractmethod
    async def run_historical(self, *args, **kwargs):
        pass
