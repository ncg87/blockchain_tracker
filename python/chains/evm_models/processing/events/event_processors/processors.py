from abc import ABC, abstractmethod
from web3 import Web3
from database import DatabaseOperator
import logging
import redis
from datetime import timedelta
from typing import Dict

logger = logging.getLogger(__name__)
class EventProcessor(ABC):
    def __init__(self, db_operator : DatabaseOperator, chain : str):
        self.protocol_map = self.create_protocol_map()
        self.logger = logger
        self.chain = chain
        self.db_operator = db_operator
        # Initialize Redis connection
        self.redis_client = redis.Redis(
            host='localhost',  # Configure as needed
            port=6379,        # Configure as needed
            db=0,            
            decode_responses=True
        )
    
    def get_cache_key(self, signature: str) -> str:
        """Generate a cache key for unknown protocols using just the signature"""
        return f"unknown_protocols:{signature}"

    def increment_unknown_protocol(self, signature: str) -> int:
        """Increment counter for unknown protocol with 24h TTL"""
        cache_key = self.get_cache_key(signature)
        pipe = self.redis_client.pipeline()
        
        # Increment and set TTL atomically
        pipe.incr(cache_key)
        pipe.expire(cache_key, timedelta(days=1))
        
        result = pipe.execute()
        return result[0]  # Return new counter value

    def get_unknown_protocols(self) -> Dict[str, int]:
        """Get all unknown protocols"""
        pattern = "unknown_protocols:*"
        keys = self.redis_client.keys(pattern)
        
        if not keys:
            return {}
            
        # Get all values in a single operation
        values = self.redis_client.mget(keys)
        
        # Extract signatures from keys and create result dict
        return {
            key.split(':')[-1]: int(value)
            for key, value in zip(keys, values)
            if value is not None
        }

    def shutdown(self):
        """Cleanup method for graceful shutdown"""
        try:
            self.redis_client.close()
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
    @abstractmethod
    def process_event(self, event):
        pass
    
    def create_protocol_map(self):
        pass