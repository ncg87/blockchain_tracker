from ..base_models import BasePipeline
from .bnb_processor import BNBProcessor
from .bnb_querier import BNBQuerier
from ..utils import decode_hex
import asyncio

class BNBPipeline(BasePipeline):
    """
    BNB pipeline class supporting asynchronous block streaming.
    """
    def __init__(self, sql_database, mongodb_database):
        super().__init__(sql_database, mongodb_database, 'BNB')
        self.querier = BNBQuerier()
        self.processor = BNBProcessor(self.sql_database, self.mongodb_database, self.querier)

    async def run(self, duration=None):
        """
        Run the pipeline in real-time mode using WebSocket streaming.
        """
        try:
            self.logger.info("Starting BNB pipeline in real-time mode...")
            tasks = []

            async for full_block in self.querier.stream_blocks(duration):
                self.logger.info(f"Received block: {decode_hex(full_block['number'])}")
                tasks.append(asyncio.create_task(self.processor.process_block(full_block)))

            await asyncio.gather(*tasks)
            self.logger.info("BNB pipeline completed in real-time mode.")
        except Exception as e:
            self.logger.error(f"Error during real-time pipeline execution: {e}", exc_info=True)

    async def run_historical(self, start_block, end_block):
        """
        Run the pipeline for a specified range of blocks.
        """
        try:
            self.logger.info(f"Starting BNB pipeline for historical range: {start_block} to {end_block}")
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
