
from ..base_models import BasePipeline
from .ethereum_processor import EthereumProcessor
from .ethereum_querier import EthereumQuerier
import asyncio
from ..utils import decode_hex


class EthereumPipeline(BasePipeline):
    """
    Ethereum pipeline class supporting asynchronous block streaming.
    """
    def __init__(self, sql_database, mongodb_database):
        super().__init__(sql_database, mongodb_database, 'Ethereum')
        self.querier = EthereumQuerier()
        self.processor = EthereumProcessor(self.sql_database, self.mongodb_database, self.querier)

    async def run(self, duration=None):
        """
        Run the pipeline in real-time mode using WebSocket streaming.
        :param duration: Duration for streaming in seconds (None for indefinite streaming).
        """
        try:
            self.logger.info("Starting Ethereum pipeline in real-time mode...")
            tasks = []  # List to hold block processing tasks

            async for full_block in self.querier.stream_blocks(duration):
                self.logger.info(f"Received block: {decode_hex(full_block.get('number'))}")
                
                # Create a new task for processing the block
                task = asyncio.create_task(self.processor.process_block(full_block))
                tasks.append(task)

            # Wait for all processing tasks to complete
            await asyncio.gather(*tasks)

            self.logger.info("Completed Ethereum pipeline in real-time mode.")
        except Exception as e:
            self.logger.error(f"Error during real-time pipeline execution: {e}", exc_info=True)

    async def run_historical(self, start_block, end_block):
        """
        Run the pipeline for a historical range of blocks.
        :param start_block: The starting block number (inclusive).
        :param end_block: The ending block number (inclusive).
        """
        try:
            self.logger.info(f"Starting Ethereum pipeline for historical range: {start_block} to {end_block}")
            current_block = start_block
            while current_block <= end_block:
                block = await self.querier.get_block(current_block)
                if block:
                    self.logger.info(f"Processing block: {decode_hex(block.get('number'))}")
                    self.processor.process_block(block)
                    current_block = block.get("number") + 1
                else:
                    self.logger.warning(f"Block {current_block} not found. Stopping pipeline.")
                    break
            self.logger.info("Completed Ethereum pipeline for historical range.")
        except Exception as e:
            self.logger.error(f"Error during historical pipeline execution: {e}", exc_info=True)
