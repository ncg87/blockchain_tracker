import asyncio
import sys
from database import SQLDatabase, MongoDatabase
from chains.ethereum import EthereumPipeline
import logging
from datetime import datetime
import os

def setup_logging(end_block: int, block_count: int):
    """
    Setup logging to both file and console with timestamp-based filename.
    
    Returns:
        str: Path to the log file
    """
    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Create timestamp-based filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"historical_blocks_{end_block}_to_{end_block-block_count+1}_{timestamp}.log"
    log_filepath = os.path.join(logs_dir, log_filename)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filepath),
            #logging.StreamHandler(sys.stdout)
        ]
    )
    
    return log_filepath

async def fetch_historical_blocks(end_block: int, block_count: int):
    """
    Fetch historical Ethereum data for a specified number of blocks.
    
    Args:
        end_block (int): The ending block number
        block_count (int): Number of blocks to fetch backwards from end_block
    """
    try:
        # Calculate start block
        start_block = max(0, end_block - block_count + 1)
        
        # Initialize databases
        sql_db = SQLDatabase()
        mongodb = MongoDatabase()
        
        # Initialize pipeline
        pipeline = EthereumPipeline(sql_db, mongodb)
        
        logger.info(f"Starting historical fetch job")
        logger.info(f"Fetching {block_count} blocks from {start_block} to {end_block}")
        
        # Run the historical pipeline
        await pipeline.run_historical(start_block, end_block)
        
        logger.info("Historical fetch job completed successfully")
        
    except Exception as e:
        logger.error(f"Error during historical data fetch: {e}", exc_info=True)
    finally:
        # Ensure cleanup
        await pipeline.cleanup()

def parse_args():
    """Parse and validate command line arguments"""
    if len(sys.argv) != 3:
        print("Usage: python fetch_historical_ethereum_blocks.py END_BLOCK BLOCK_COUNT")
        print("Example: python fetch_historical_ethereum_blocks.py 19000000 1000")
        sys.exit(1)
    
    try:
        end_block = int(sys.argv[1])
        block_count = int(sys.argv[2])
        
        if end_block < 0 or block_count <= 0:
            raise ValueError("Block numbers must be positive")
            
        return end_block, block_count
    
    except ValueError as e:
        logger.error(f"Invalid arguments: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Parse arguments first
    end_block, block_count = parse_args()
    
    # Setup logging
    log_file = setup_logging(end_block, block_count)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Log file created at: {log_file}")
    logger.info(f"Script started with parameters: end_block={end_block}, block_count={block_count}")
    
    # Run the async function
    asyncio.run(fetch_historical_blocks(end_block, block_count)) 