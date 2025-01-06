from abc import ABC, abstractmethod
from web3 import Web3
from config import Settings
import logging

logger = logging.getLogger(__name__)

class BaseQuerier(ABC):
    """
    Base class for all blockchain queriers.
    """
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(Settings.QUICKNODE_ENDPOINT))
        self.logger = logger

    def is_connected(self) -> bool:
        """
        Check if the connection to the provider is successful.
        """
        return self.w3.is_connected()

    @abstractmethod
    def get_block(self, block_number: int = None):
        """
        Abstract method to get a block. Subclasses must implement this.
        """
        pass
