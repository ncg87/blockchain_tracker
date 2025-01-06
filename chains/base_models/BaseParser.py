from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class BaseParser(ABC):
    """
    Base class for all blockchain parsers.
    """
    def __init__(self, database):
        self.database = database
        self.logger = logger