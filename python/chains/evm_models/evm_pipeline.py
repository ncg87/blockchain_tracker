from ..base_models import BasePipeline
import asyncio
from ..utils import decode_hex
import signal
import threading
import time
import os

class EVMPipeline(BasePipeline):
    """
    Abstract EVM pipeline class with common functionality.
    """
    def __init__(self, sql_database, mongodb_database, network_name: str, querier, processor):
        super().__init__(sql_database, mongodb_database, network_name)
        self.querier = querier
        self.processor = processor
        self.network = network_name
        self._shutdown_flag = threading.Event()
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}. Starting graceful shutdown...")
        self.shutdown()

    def schedule_shutdown(self, delay_seconds=86400):
        """Schedule an automatic shutdown after specified hours"""
        def shutdown_timer():
            time.sleep(delay_seconds)  # Convert hours to seconds
            self.logger.info(f"Automatic shutdown triggered after {delay_seconds} seconds")
            self.shutdown()

        shutdown_thread = threading.Thread(target=shutdown_timer, daemon=True)
        shutdown_thread.start()

    async def run(self, duration=None):
        """
        Run the pipeline in real-time mode using WebSocket streaming.
        """
        try:
            self.logger.info(f"Starting {self.network} pipeline in real-time mode...")
            tasks = []

            # Schedule shutdown if duration is specified
            if duration:
                self.schedule_shutdown(delay_seconds=duration)

            async for full_block in self.querier.stream_blocks(duration):
                if self._shutdown_flag.is_set():
                    self.logger.info("Shutdown flag detected, stopping pipeline...")
                    break
                    
                self.logger.info(f"Received block: {decode_hex(full_block.get('number'))}")
                tasks.append(asyncio.create_task(self.processor.process_block(full_block)))

            # Wait for remaining tasks to complete
            if tasks:
                await asyncio.gather(*tasks)
                
            self.logger.info(f"Completed {self.network} pipeline in real-time mode.")
            
        except Exception as e:
            self.logger.error(f"Error during real-time pipeline execution: {e}", exc_info=True)
        finally:
            if self._shutdown_flag.is_set():
                await self.cleanup()

    async def run_historical(self, start_block, end_block):
        """
        Run the pipeline for a historical range of blocks.
        """
        try:
            self.logger.info(f"Starting {self.network} pipeline for historical range: {start_block} to {end_block}")
            current_block = start_block
            while current_block <= end_block and not self._shutdown_flag.is_set():
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
        finally:
            if self._shutdown_flag.is_set():
                await self.cleanup()

    def shutdown(self):
        """Initiate shutdown sequence"""
        self.logger.info("Initiating pipeline shutdown...")
        self._shutdown_flag.set()
        
        # Trigger processor shutdown
        if hasattr(self.processor, 'shutdown'):
            self.processor.shutdown()
            
        # Trigger querier shutdown if it has a shutdown method
        if hasattr(self.querier, 'shutdown'):
            self.querier.shutdown()

    async def cleanup(self):
        """Cleanup resources during shutdown"""
        try:
            self.logger.info("Cleaning up pipeline resources...")
            
            # Close database connections
            if hasattr(self, 'sql_database'):
                self.sql_database.close()
            if hasattr(self, 'mongodb_database'):
                await self.mongodb_database.close()
                
            self.logger.info("Pipeline cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during pipeline cleanup: {e}", exc_info=True)
        finally:
            # Force exit if cleanup takes too long
            if time.time() - self._shutdown_flag > 65:  # 5 second grace period
                self.logger.warning("Forcing exit after timeout")
                os._exit(0)