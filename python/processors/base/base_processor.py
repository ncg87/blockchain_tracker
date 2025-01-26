from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio
import logging
from redis import Redis
from constants import TIME_WINDOWS, TimeWindow

logger = logging.getLogger(__name__)

class BaseTimeSeriesProcessor(ABC):
    def __init__(
        self,
        cache_manager,  # Will be your cache manager once implemented
        db_client,      # Your database client
        time_windows: Dict[str, TimeWindow] = TIME_WINDOWS
    ):
        self.cache = cache_manager
        self.db = db_client
        self.time_windows = time_windows
        self.tasks = []
        self.is_running = False
        self.redis_client = Redis(host='localhost', port=6379, db=0)

    async def start(self):
        """Start all update tasks for different time windows"""
        self.is_running = True
        self.tasks = [
            asyncio.create_task(self._run_window_updates(window_key, window))
            for window_key, window in self.time_windows.items()
        ]
        await asyncio.gather(*self.tasks)

    async def stop(self):
        """Stop all update tasks"""
        self.is_running = False
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)

    async def _run_window_updates(self, window_key: str, window: TimeWindow):
        """Run updates for a specific time window"""
        while self.is_running:
            try:
                await self._process_window(window_key, window)
                await asyncio.sleep(window.update_frequency.total_seconds())
            except Exception as e:
                logger.error(f"Error processing {window_key} window: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    @abstractmethod
    async def _process_window(self, window_key: str, window: TimeWindow):
        """Process data for a specific time window"""
        pass