from abc import ABC, abstractmethod
import logging

from database import SQLDatabase, SQLInsertOperations, SQLQueryOperations, SQLOperator
from database import MongoDatabase, MongoInsertOperations, MongoQueryOperations, MongoDBOperator
from database import DatabaseOperator
logger = logging.getLogger(__name__)

class BaseProcessor(ABC):
    """
    Base class for all blockchain processors.
    """
    def __init__(self, sql_database, mongodb_database, network):
        
        self.db_operator = DatabaseOperator(sql_database, mongodb_database)
        
        # Network
        self.network = network
        
        # Logger
        self.logger = logger
        self.logger.info(f"Initialized {self.network} processor")