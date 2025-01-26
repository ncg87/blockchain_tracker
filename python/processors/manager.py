from typing import List
from .token_processor import TokenProcessor
from .dex_processor import DEXProcessor
from .base_processor import BaseTimeSeriesProcessor

class ProcessorManager:
    def __init__(
        self,
        cache_manager,
        db_client
    ):
        self.cache = cache_manager
        self.db = db_client
        self.processors: List[BaseTimeSeriesProcessor] = [
            TokenProcessor(
                cache_manager=self.cache,
                db_client=self.db
            ),
            DEXProcessor(
                cache_manager=self.cache,
                db_client=self.db
            )
        ]

    async def start(self):
        """Initialize and start all processors"""
        self.processors = [
            TokenProcessor(
                cache_manager=self.cache,
                db_client=self.db
            ),
            DexProcessor(
                cache_manager=self.cache,
                db_client=self.db
            )
        ]

        logger.info("Starting processors...")
        await asyncio.gather(
            *[processor.start() for processor in self.processors]
        )

    async def stop(self):
        """Stop all processors"""
        logger.info("Stopping processors...")
        await asyncio.gather(
            *[processor.stop() for processor in self.processors]
        )