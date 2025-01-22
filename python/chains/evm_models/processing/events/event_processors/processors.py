from abc import ABC, abstractmethod
from web3 import Web3
import logging

logger = logging.getLogger(__name__)
class EventProcessor(ABC):
    def __init__(self):
        self.protocol_map = self.create_protocol_map()
        self.logger = logger
    @abstractmethod
    def process_event(self, event):
        pass
    
    def create_protocol_map(self):
        pass