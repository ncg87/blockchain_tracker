from typing import Dict, Any

# Global cache instance
_cache: Dict[str, Any] = {}

def get_cache() -> Dict[str, Any]:
    """Get the global cache instance"""
    global _cache
    return _cache

def set_cache(new_cache: Dict[str, Any]) -> None:
    """Set the global cache instance"""
    global _cache
    _cache = new_cache

def update_cache(key: str, value: Any) -> None:
    """Update a specific key in the cache"""
    global _cache
    _cache[key] = value

def get_cache_value(key: str, default: Any = None) -> Any:
    """Get a value from cache with a default fallback"""
    return _cache.get(key, default) 