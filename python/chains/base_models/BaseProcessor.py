from abc import ABC, abstractmethod
import logging

from database import SQLDatabase, SQLInsertOperations, SQLQueryOperations, SQLOperator
from database import MongoDatabase, MongoInsertOperations, MongoQueryOperations, MongoDBOperator
logger = logging.getLogger(__name__)

class BaseProcessor(ABC):
    """
    Base class for all blockchain processors.
    """
    def __init__(self, sql_database, mongodb_database, network):
        
        # SQL Database operations
        self.sql_insert_ops = SQLInsertOperations(sql_database)
        self.sql_query_ops = SQLQueryOperations(sql_database)
        
        self.sql_operator = SQLOperator(sql_database)
        self.mongodb_operator = MongoDBOperator(mongodb_database)
        
        # MongoDB Database operations
        self.mongodb_insert_ops = MongoInsertOperations(mongodb_database)
        self.mongodb_query_ops = MongoQueryOperations(mongodb_database)
        
        # Network
        self.network = network
        
        # Logger
        self.logger = logger
        self.logger.info(f"Initialized {self.network} processor")