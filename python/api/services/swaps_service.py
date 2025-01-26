from ..core.base_service import BaseService
from database import SQLDatabase, SQLQueryOperations
import logging
from ..utils.logging import log_execution_time
from typing import Dict
import time

class SwapsService(BaseService):
    def __init__(self):
        super().__init__("swaps")
        self.db = SQLDatabase()
        self._cache = {}
        self._cache_ttl = 60  # Cache TTL in seconds
        self.logger = logging.getLogger(__name__)
        self.logger.info("SwapsService initialized")
        self.ops = SQLQueryOperations(self.db)
        self._token_cache = {}

    async def initialize(self) -> None:
        self.logger.info("No initialization required for SwapsService")
        pass
    
    async def cleanup(self) -> None:
        self.logger.info("Cleaning up SwapsService")
        self._cache.clear()
        
    INTERVALS = {
        "5m": 300,
        "1h": 3600,
        "24h": 86400,
        "1w": 604800,
    }

    def _get_cache_key(self, network: str, interval: str, points: int) -> str:
        """Generate a cache key"""
        return f"{network}:{interval}:{points}"

    def _get_cached_data(self, cache_key: str):
        """Get data from cache if it exists and is not expired"""
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return data
            else:
                del self._cache[cache_key]
        return None
    
    def validate_network(self, network: str):
        """Validate network name"""
        VALID_NETWORKS = {'Ethereum', 'Arbitrum', 'BNB', 'Base'}
        if network not in VALID_NETWORKS:
            raise ValueError(f"Invalid network: {network}. Valid networks are: {', '.join(sorted(VALID_NETWORKS))}")
        return network

    @log_execution_time(lambda self: self.logger)
    async def get_swaps(self, network: str, interval) -> Dict[str, Dict[str, str]]:
        """Get swaps for a specific network and time interval"""
        self.logger.debug(f"Fetching swaps for {network} in {interval} interval")
        result = {}
        
        for interval_name, seconds in self.INTERVALS.items():
            self.logger.debug(f"Fetching {interval_name} interval data")
            swaps = self.ops.api.get_all_networks_swaps(seconds)
            result[interval_name] = {
                network: f"{swaps:.4f}" 
                for network, swaps in swaps.items()
            }
        return result
