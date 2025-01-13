from ..base_models import BasePipeline
import asyncio
from ..utils import decode_hex

class EVMPipeline(BasePipeline):
    """
    Abstract EVM pipeline class with common functionality.
    """
    def __init__(self, sql_database, mongodb_database, network_name: str, querier, processor):
        super().__init__(sql_database, mongodb_database, network_name)
        self.querier = querier
        self.processor = processor
        self.network = network_name

    async def run(self, duration=None):
        """
        Run the pipeline in real-time mode using WebSocket streaming.
        """
        try:
            self.logger.info(f"Starting {self.network} pipeline in real-time mode...")
            tasks = []

            async for full_block in self.querier.stream_blocks(duration):
                self.logger.info(f"Received block: {decode_hex(full_block.get('number'))}")
                tasks.append(asyncio.create_task(self.processor.process_block(full_block)))

            await asyncio.gather(*tasks)
            self.logger.info(f"Completed {self.network} pipeline in real-time mode.")
        except Exception as e:
            self.logger.error(f"Error during real-time pipeline execution: {e}", exc_info=True)

    async def run_historical(self, start_block, end_block):
        """
        Run the pipeline for a historical range of blocks.
        """
        try:
            self.logger.info(f"Starting {self.network} pipeline for historical range: {start_block} to {end_block}")
            current_block = start_block
            while current_block <= end_block:
                block = await self.querier.get_block(current_block)
                if block:
                    self.logger.info(f"Processing block: {decode_hex(block.get('number'))}")
                    await self.processor.process_block(block)
                    current_block = block.get("number") + 1
                else:
                    self.logger.warning(f"Block {current_block} not found. Stopping pipeline.")
                    break
            self.logger.info(f"Completed {self.network} pipeline for historical range.")
        except Exception as e:
            self.logger.error(f"Error during historical pipeline execution: {e}", exc_info=True)