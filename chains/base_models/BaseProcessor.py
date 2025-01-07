from abc import ABC, abstractmethod
import logging

from database import InsertOperations, QueryOperations

logger = logging.getLogger(__name__)

class BaseProcessor(ABC):
    """
    Base class for all blockchain processors.
    """
    def __init__(self, database, network):
        
        # Database operations
        self.insert_ops = InsertOperations(database)
        self.query_ops = QueryOperations(database)
        
        # Network
        self.network = network
        
        # Logger
        self.logger = logger
        self.logger.info(f"Initialized {self.network} processor")