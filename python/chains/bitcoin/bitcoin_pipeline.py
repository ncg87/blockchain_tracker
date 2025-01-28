from ..base_models import BasePipeline
from .bitcoin_processor import BitcoinProcessor
from .bitcoin_querier import BitcoinQuerier
import asyncio


class BitcoinPipeline(BasePipeline):
    """
    Bitcoin pipeline class supporting asynchronous block streaming.
    """

    def __init__(self, sql_database, mongodb_database):
        super().__init__(sql_database, mongodb_database, 'bitcoin')
        self.querier = BitcoinQuerier()
        self.processor = BitcoinProcessor(self.sql_database, self.mongodb_database, self.querier)

    async def run(self, duration=None):
        """
        Run the pipeline in real-time mode using block polling.
        :param duration: Duration for streaming in seconds (None for indefinite streaming).
        """
        try:
            self.logger.info("Starting Bitcoin pipeline in real-time mode...")
            tasks = []  # List to hold block processing tasks

            async for full_block in self.querier.stream_blocks(duration):
                self.logger.info(f"Received block: {full_block.get('hash')}")

                # Create a new task for processing the block
                task = asyncio.create_task(self.processor.process_block(full_block))
                tasks.append(task)

            # Wait for all processing tasks to complete
            await asyncio.gather(*tasks)

            self.logger.info("Completed Bitcoin pipeline in real-time mode.")
        except Exception as e:
            self.logger.error(f"Error during real-time pipeline execution: {e}", exc_info=True)

    async def run_historical(self, start_block, end_block = None):
        """
        Run the pipeline for a historical range of blocks.
        :param start_block: The starting block number (inclusive).
        :param end_block: The ending block number (inclusive).
        """
        
        # Base initialization of the end block
        if end_block is None:
            end_block = start_block + 100
        
        try:
            self.logger.info(f"Starting Bitcoin pipeline for historical range: {start_block} to {end_block}")
            current_block = start_block
            while current_block <= end_block:
                block = await self.querier.get_block(current_block)
                if block:
                    self.logger.info(f"Processing block: {block.get('height')}")
                    await self.processor.process_block(block)
                    current_block += 1
                else:
                    self.logger.warning(f"Block {current_block} not found. Stopping pipeline.")
                    break
            self.logger.info("Completed Bitcoin pipeline for historical range.")
        except Exception as e:
            self.logger.error(f"Error during historical pipeline execution: {e}", exc_info=True)
