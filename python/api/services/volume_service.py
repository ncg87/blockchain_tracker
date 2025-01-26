from ..core.base_service import BaseService
from ..utils.logging import log_execution_time
from typing import Dict, List, Any
from database import SQLQueryOperations, SQLDatabase
import time
import logging

VALID_NETWORKS = {'Ethereum', 'Arbitrum', 'BNB', 'Base'}  # Add your valid networks here

class VolumeService(BaseService):
    def __init__(self):
        super().__init__("volume")
        self.db = SQLDatabase()
        self._cache = {}
        self._cache_ttl = 60  # Cache TTL in seconds
        self.logger = logging.getLogger(__name__)
        self.logger.info("VolumeService initialized")

    async def initialize(self) -> None:
        self.logger.info("No initialization required for VolumeService")
        pass

    async def cleanup(self) -> None:
        self.logger.info("Cleaning up VolumeService")
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
        # Create a case-sensitive set of valid networks
        VALID_NETWORKS = {'Ethereum', 'Arbitrum', 'BNB', 'Base'}
        
        if network not in VALID_NETWORKS:
            raise ValueError(f"Invalid network: {network}. Valid networks are: {', '.join(sorted(VALID_NETWORKS))}")
        return network

    @log_execution_time(lambda self: self.logger)
    async def get_all_volumes(self) -> Dict[str, Dict[str, str]]:
        """Get volumes for all networks across different time intervals"""
        self.logger.debug("Fetching volumes for all networks")
        ops = SQLQueryOperations(self.db)
        result = {}
        
        for interval_name, seconds in self.INTERVALS.items():
            self.logger.debug(f"Fetching {interval_name} interval data")
            volumes = ops.api.get_all_networks_volume(seconds)
            result[interval_name] = {
                network: f"{volume:.4f}" 
                for network, volume in volumes.items()
            }
        
        return result
    
    @log_execution_time(lambda self: self.logger)
    async def get_volume_of_all_tokens(self, network: str, interval: str, points: int) -> Dict[str, float]:
        """Get volume of all tokens for a specific network"""
        ops = SQLQueryOperations(self.db)
        return ops.api.get_historical_token_volume(network, self.INTERVALS[interval], points)
    
    @log_execution_time(lambda self: self.logger)
    async def get_network_stats(self, network: str, interval: str) -> Dict[str, float]:
        """Get comprehensive stats for a specific network"""
        if interval not in self.INTERVALS:
            raise ValueError("Invalid interval")
        
        ops = SQLQueryOperations(self.db)
        return ops.api.get_network_stats(network, self.INTERVALS[interval])
    
    @log_execution_time(lambda self: self.logger)
    async def get_all_fees(self) -> Dict[str, Dict[str, str]]:
        """Get fees for all networks across different time intervals"""
        ops = SQLQueryOperations(self.db)
        result = {}
        
        for interval_name, seconds in self.INTERVALS.items():
            fees = ops.api.get_all_networks_fees(seconds)
            result[interval_name] = {
                network: f"{fee:.4f}" 
                for network, fee in fees.items()
            }
        
        return result

    @log_execution_time(lambda self: self.logger)
    async def get_all_tx_counts(self) -> Dict[str, Dict[str, int]]:
        """Get transaction counts for all networks across different time intervals"""
        ops = SQLQueryOperations(self.db)
        result = {}
        
        for interval_name, seconds in self.INTERVALS.items():
            counts = ops.api.get_all_networks_tx_count(seconds)
            result[interval_name] = counts
        
        return result

    @log_execution_time(lambda self: self.logger)
    async def get_network_historical_data(self, network: str, interval: str, points: int = 24) -> Dict[str, Any]:
        """Get historical data for a specific network with caching"""
        if interval not in self.INTERVALS:
            self.logger.error(f"Invalid interval requested: {interval}")
            raise ValueError(f"Invalid interval. Must be one of: {list(self.INTERVALS.keys())}")
        
        try:
            self.validate_network(network)
            self.logger.info(f"Cache miss for {self._get_cache_key(network, interval, points)}")
            ops = SQLQueryOperations(self.db)
            data = ops.api.get_network_historical_data(
                network, 
                self.INTERVALS[interval], 
                points
            )
            
            if not data:
                self.logger.warning(f"No data found for network: {network}")
                raise ValueError(f"No data found for network: {network}")
            
            result = {
                "chain": network,
                "interval": interval,
                "data": [
                    {
                        "timestamp": int(point["timestamp"]),
                        "volume": float(point["volume"]),
                        "fees": float(point["fees"]),
                        "transactions": int(point["transactions"])
                    }
                    for point in data
                ]
            }
            
            # Cache the result
            self._cache[self._get_cache_key(network, interval, points)] = (result, time.time())
            
            return result
        except Exception as e:
            self.logger.error(f"Error in get_network_historical_data: {str(e)}", exc_info=True)
            raise

    def invalidate_cache(self, network: str = None, interval: str = None):
        """Clear the cached results, optionally for specific network/interval"""
        if network is None and interval is None:
            self._cache.clear()
        else:
            keys_to_delete = []
            for key in self._cache.keys():
                if network and network in key:
                    keys_to_delete.append(key)
                elif interval and interval in key:
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self._cache[key]
