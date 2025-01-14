from abc import ABC, abstractmethod
import logging

class BaseQuerier(ABC):
    """
    Base class for all blockchain queriers.
    """
    def __init__(self, network):
        self.logger = logging.getLogger(__name__)
        self.network = network
        self.logger.info(f"Initialized {self.network} querier")

    @abstractmethod
    def get_block(self, block_number: int = None):
        """
        Abstract method to get a block. Subclasses must implement this.
        """
        pass
