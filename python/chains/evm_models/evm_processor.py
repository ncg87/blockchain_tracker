from ..base_models import BaseProcessor
import threading
from psycopg2.pool import ThreadedConnectionPool
from config import Settings
import signal
import time
from .processing import EventProcessor, BlockProcessor, LogProcessor

class EVMProcessor(BaseProcessor):
    """
    Abstract EVM processor class with common functionality.
    """
    def __init__(self, sql_database, mongodb_database, network_name: str, querier):
        super().__init__(sql_database, mongodb_database, network_name)
        self.querier = querier
        self.event_processor = EventProcessor(sql_database, mongodb_database, network_name)
        self.block_processor = BlockProcessor(self.db_operator, network_name)
        self.log_processor = LogProcessor(self.db_operator, self.querier, network_name)

        # Initialize connection pool
        self.db_pool = ThreadedConnectionPool(
            minconn=5,
            maxconn=20,
            **Settings.POSTGRES_CONFIG
        )
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}. Starting graceful shutdown...")
        self.shutdown()

    def schedule_shutdown(self, delay_seconds=86400):  # Default 24 hours in seconds
        """Schedule an automatic shutdown after specified seconds"""
        def shutdown_timer():
            time.sleep(delay_seconds)
            self.logger.info(f"Automatic shutdown triggered after {delay_seconds} seconds")
            self.shutdown()

        shutdown_thread = threading.Thread(target=shutdown_timer, daemon=True)
        shutdown_thread.start()

    async def process_block(self, block):
        """Process a block, transactions and logs."""
        try:
            # Get block info immediately - this is synchronous and fast
            block_number, timestamp = self.block_processor.process(block)
            
            # Get logs for the block - synchronous operation
            logs = self.querier.get_block_logs(block_number)
            
            # Process logs synchronously since it's mainly data transformation
            decoded_logs = await self.log_processor.process(block_number, timestamp, logs)
            
            # Let event processor handle all the event processing logic

            processed_events = await self.event_processor.process_block_events(decoded_logs, timestamp)
            
            return decoded_logs, processed_events
            
        except Exception as e:
            self.logger.error(f"Error processing block {block_number}: {e}", exc_info=True)
            raise

    def shutdown(self):
        """Cleanup method for graceful shutdown"""
        try:
            # Shutdown event processor first
            if hasattr(self, 'event_processor'):
                self.event_processor.shutdown()
            
            # Close database pool
            if hasattr(self, 'db_pool'):
                self.db_pool.closeall()
                
            self.logger.info("Processor shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")