from abc import ABC, abstractmethod
from web3 import Web3
from database import SQLDatabase, SQLQueryOperations, SQLInsertOperations
import logging

logger = logging.getLogger(__name__)
class EventProcessor(ABC):
    def __init__(self, sql_db, network):
        self.protocol_map = self.create_protocol_map()
        self.logger = logger
        self.network = network
        self.sql_query_ops = SQLQueryOperations(sql_db)
        self.sql_insert_ops = SQLInsertOperations(sql_db)
    @abstractmethod
    def process_event(self, event):
        pass
    
    def create_protocol_map(self):
        pass