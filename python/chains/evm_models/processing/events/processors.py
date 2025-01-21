from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from web3 import Web3
from .models import BaseEvent, Transfer, Swap

class EventProcessor(ABC):
    def __init__(self, sql_query_ops=None):
        self.sql_query_ops = sql_query_ops

    @abstractmethod
    def process(self, event: Dict, network: str) -> Optional[BaseEvent]:
        pass

    @abstractmethod
    def get_parameter_mapping(self) -> Dict[str, List[str]]:
        pass

    def get_parameter_value(self, parameters: Dict, param_type: str) -> Any:
        possible_keys = self.get_parameter_mapping().get(param_type, [])
        for key in possible_keys:
            if key in parameters:
                return parameters[key]['value']
        raise KeyError(f"No matching {param_type} parameter found")