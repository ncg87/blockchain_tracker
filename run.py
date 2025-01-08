import asyncio
from chains import EthereumPipeline, BNBPipeline, BitcoinPipeline, SolanaPipeline
from database import Database

async def main():
    database = Database()

    # Initialize pipelines, 
    # ## *** make a factory for this *** ## #
    ethereum_pipeline = EthereumPipeline(database)
    bnb_pipeline = BNBPipeline(database)
    bitcoin_pipeline = BitcoinPipeline(database)
    solana_pipeline = SolanaPipeline(database)

    # Run both pipelines concurrently
    await asyncio.gather(
        ethereum_pipeline.run(duration=60),  # Ethereum for 60 seconds
        bnb_pipeline.run(duration=60),    # Solana for 60 seconds
        bitcoin_pipeline.run(duration=60),  # Bitcoin for 60 seconds
        solana_pipeline.run(duration=60),  # Solana for 60 seconds
    )

asyncio.run(main())
