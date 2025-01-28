from ..base_models import BasePipeline
from .solana_querier import SolanaQuerier
from .solana_processor import SolanaProcessor
import asyncio

class SolanaPipeline(BasePipeline):
    """
    Solana pipeline class supporting asynchronous block streaming.
    """
    def __init__(self, sql_database, mongodb_database):
        super().__init__(sql_database, mongodb_database, 'solana')
        self.querier = SolanaQuerier()
        self.processor = SolanaProcessor(sql_database, mongodb_database, self.querier)

    async def run(self, duration=None):
        """
        Run the pipeline in real-time mode using WebSocket streaming.
        :param duration: Duration for streaming in seconds (None for indefinite streaming).
        """
        try:
            self.logger.info("Starting Solana pipeline in real-time mode...")
            tasks = []  # List to hold block processing tasks

            async for full_block in self.querier.stream_blocks(duration):
                self.logger.info(f"Received block for slot: {full_block.get('blockHeight')}")
                
                # Create a new task for processing the block
                task = asyncio.create_task(self.processor.process_block(full_block))
                tasks.append(task)

            # Wait for all processing tasks to complete
            await asyncio.gather(*tasks)

            self.logger.info("Completed Solana pipeline in real-time mode.")
        except Exception as e:
            self.logger.error(f"Error during real-time pipeline execution: {e}", exc_info=True)

    async def run_historical(self, start_slot, end_slot):
        """
        Run the pipeline for a historical range of slots.
        :param start_slot: The starting slot number (inclusive).
        :param end_slot: The ending slot number (inclusive).
        """
        try:
            self.logger.info(f"Starting Solana pipeline for historical range: {start_slot} to {end_slot}")
            current_slot = start_slot
            while current_slot <= end_slot:
                block = await self.querier.get_block(current_slot)
                if block:
                    self.logger.info(f"Processing block for slot: {block.get('slot')}")
                    await self.processor.process_block(block)
                    current_slot += 1
                else:
                    self.logger.warning(f"Block for slot {current_slot} not found. Stopping pipeline.")
                    break
            self.logger.info("Completed Solana pipeline for historical range.")
        except Exception as e:
            self.logger.error(f"Error during historical pipeline execution: {e}", exc_info=True)
