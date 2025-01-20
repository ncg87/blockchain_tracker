import logging
import asyncio
from functools import wraps
import time
from typing import Any, Callable

def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Configure and return a logger instance"""
    logger = logging.getLogger(name)
    level = getattr(logging, level.upper())
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def log_execution_time(get_logger: Callable[..., logging.Logger]):
    """Decorator to log method execution time"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = await func(self, *args, **kwargs)
                execution_time = time.time() - start_time
                get_logger(self).debug(
                    f"{func.__name__} executed in {execution_time:.2f} seconds"
                )
                return result
            except Exception as e:
                get_logger(self).error(
                    f"Error in {func.__name__}: {str(e)}",
                    exc_info=True
                )
                raise
                
        @wraps(func)
        def sync_wrapper(self, *args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(self, *args, **kwargs)
                execution_time = time.time() - start_time
                get_logger(self).debug(
                    f"{func.__name__} executed in {execution_time:.2f} seconds"
                )
                return result
            except Exception as e:
                get_logger(self).error(
                    f"Error in {func.__name__}: {str(e)}",
                    exc_info=True
                )
                raise
                
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator 