import asyncio
from chains import EthereumPipeline, BNBPipeline, BitcoinPipeline, SolanaPipeline, XRPPipeline, BaseChainPipeline
from database import SQLDatabase, MongoDatabase
import logging

# General logging setup for maintenance.log
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("maintenance.log", mode='w'),  # Reset on each run
        #logging.StreamHandler()  # Optional: Logs to the console
    ]
)

# Setup error-specific logger for error.log
error_logger = logging.getLogger("error_logger")
error_logger.setLevel(logging.ERROR)
error_handler = logging.FileHandler("error.log", mode='w')  # Reset on each run
error_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
error_logger.addHandler(error_handler)

async def main():
    try:
        sql_database = SQLDatabase()
        mongodb_database = MongoDatabase()

        # Initialize pipelines
        ethereum_pipeline = EthereumPipeline(sql_database, mongodb_database)
        bnb_pipeline = BNBPipeline(sql_database, mongodb_database)
        bitcoin_pipeline = BitcoinPipeline(sql_database, mongodb_database)
        solana_pipeline = SolanaPipeline(sql_database, mongodb_database)
        xrp_pipeline = XRPPipeline(sql_database, mongodb_database)
        base_pipeline = BaseChainPipeline(sql_database, mongodb_database)

        duration = 21600

        # Run all pipelines concurrently
        await asyncio.gather(
            ethereum_pipeline.run(duration=duration),
            bnb_pipeline.run(duration=duration),
            base_pipeline.run(duration=duration),
            bitcoin_pipeline.run(duration=duration),
            #solana_pipeline.run(duration=1200),
            xrp_pipeline.run(duration=duration),
        )
    except Exception as e:
        # Log any errors
        error_logger.error("An error occurred", exc_info=True)

# Run the program
asyncio.run(main())
