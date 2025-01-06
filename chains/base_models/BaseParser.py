from abc import ABC, abstractmethod

class BaseParser(ABC):
    @abstractmethod
    def parse(self, data: str):
        pass