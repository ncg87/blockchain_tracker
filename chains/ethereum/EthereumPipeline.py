import logging
from ..base_models import BasePipeline
from .EthereumParser import EthereumParser
from .EthereumQuerier import EthereumQuerier

logger = logging.getLogger(__name__)

class EthereumPipeline(BasePipeline):
    def __init__(self, database, logger=None):
        """
        Initialize the Ethereum pipeline.
        """
        self.logger = logger
        self.database = database
        self.querier = EthereumQuerier()
        self.parser = EthereumParser(self.database, self.querier)

    def run(self, start_block=None, end_block=None):
        """
        Run the pipeline for a range of blocks.
        :param start_block: The starting block number (inclusive).
        :param end_block: The ending block number (inclusive). If None, only the start_block will be processed.
        """
        try:
            self.logger.info("Starting Ethereum pipeline...")
            
            # Determine the block range to process
            current_block = start_block
            while current_block <= end_block or (end_block is None and current_block is not None):
                self.logger.info(f"Processing block {current_block}")
                
                # Fetch the block
                block = self.querier.get_block(current_block)
                
                # Process the block
                self.parser.process_block(block)
                
                # Move to the next block
                current_block = block.get("number") + 1 if block else None
            
            self.logger.info("Ethereum pipeline completed successfully.")
        except Exception as e:
            self.logger.error(f"An error occurred during the Ethereum pipeline execution: {e}", exc_info=True)
            raise
