from abc import ABC, abstractmethod
from web3 import Web3

class BaseQuerier(ABC):
    """
    Base class for all blockchain queriers.
    """
    def __init__(self, provider: str):
        self.provider = provider
        self.w3 = Web3(Web3.HTTPProvider(provider))

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
