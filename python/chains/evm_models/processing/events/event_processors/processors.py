from abc import ABC, abstractmethod
from web3 import Web3
from database import DatabaseOperator
import logging

logger = logging.getLogger(__name__)
class EventProcessor(ABC):
    def __init__(self, db_operator : DatabaseOperator, chain : str):
        self.protocol_map = self.create_protocol_map()
        self.logger = logger
        self.chain = chain
        self.db_operator = db_operator
    @abstractmethod
    def process_event(self, event):
        pass
    
    def create_protocol_map(self):
        pass