from abc import ABC, abstractmethod
from typing import Any
from ..utils.logging import setup_logger

class BaseService(ABC):
    def __init__(self, service_name: str):
        self.logger = setup_logger(f"service.{service_name}")
        
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize service resources"""
        pass
        
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup service resources"""
        pass 