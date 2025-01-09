from ..base_models import BasePipeline
from .xrp_querier import XRPQuerier
from .xrp_processor import XRPProcessor
import asyncio
class XRPPipeline(BasePipeline):
    """
    XRP-specific pipeline for processing ledger data.
    """
    def __init__(self, sql_database, mongodb_database):
        super().__init__(sql_database, mongodb_database, 'XRP')
        self.querier = XRPQuerier()
        self.processor = XRPProcessor(sql_database, mongodb_database, self.querier)

    async def run(self, duration=None):
        """
        Run the pipeline in real-time mode using WebSocket streaming.
        :param duration: Duration for streaming in seconds (None for indefinite streaming).
        """
        try:
            self.logger.info("Starting XRP pipeline in real-time mode...")
            tasks = []  # List to hold ledger processing tasks

            async for full_ledger in self.querier.stream_blocks(duration):
                self.logger.info(f"Received ledger: {full_ledger['ledger_index']}")

                # Create a new task for processing the ledger
                task = asyncio.create_task(self.processor.process_block(full_ledger))
                tasks.append(task)

            # Wait for all processing tasks to complete
            await asyncio.gather(*tasks)

            self.logger.info("Completed XRP pipeline in real-time mode.")
        except Exception as e:
            self.logger.error(f"Error during real-time pipeline execution: {e}", exc_info=True)

    async def run_historical(self, start_ledger, end_ledger):
        """
        Run the pipeline for a historical range of ledgers.
        :param start_ledger: The starting ledger index (inclusive).
        :param end_ledger: The ending ledger index (inclusive).
        """
        try:
            self.logger.info(f"Starting XRP pipeline for historical range: {start_ledger} to {end_ledger}")
            current_ledger = start_ledger
            while current_ledger <= end_ledger:
                ledger = await self.querier.get_block(current_ledger)
                if ledger:
                    self.logger.info(f"Processing ledger: {ledger.get('ledger_index')}")
                    await self.processor.process_block(ledger)
                    current_ledger += 1
                else:
                    self.logger.warning(f"Ledger {current_ledger} not found. Stopping pipeline.")
                    break
            self.logger.info("Completed XRP pipeline for historical range.")
        except Exception as e:
            self.logger.error(f"Error during historical pipeline execution: {e}", exc_info=True)