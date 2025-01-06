from abc import ABC, abstractmethod
import logging
class BasePipeline(ABC):
    @abstractmethod
    def run(self, *args, **kwargs):
        pass