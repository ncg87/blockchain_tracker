import asyncio
from chains import (EthereumPipeline, BNBPipeline, BitcoinPipeline, SolanaPipeline, XRPPipeline, BaseChainPipeline, ArbitrumPipeline,
                    PolygonChainPipeline, OptimismChainPipeline, AvalancheChainPipeline, PolygonZKPipeline, ZkSyncPipeline, MantlePipeline,
                    LineaPipeline
                    )
from database import SQLDatabase, MongoDatabase
import logging
import signal
import sys


# General logging setup for maintenance.log
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("maintenance.log", mode='w', encoding='utf-8'),
        #logging.StreamHandler()  # Optional: Logs to the console
    ]
)

# Add a list to track active pipelines
active_pipelines = []

async def cleanup(pipelines):
    """Cleanup function to properly close all pipeline connections"""
    logging.info("Starting cleanup...")  # Add debug print
    cleanup_tasks = []
    for pipeline in pipelines:
        if hasattr(pipeline, 'websocket_handler'):
            cleanup_tasks.append(pipeline.websocket_handler.stop())
    if cleanup_tasks:
        await asyncio.gather(*cleanup_tasks)
    logging.info("Cleanup completed")  # Add debug print

async def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logging.info("Received shutdown signal, cleaning up...")
    await cleanup(active_pipelines)
    # Force exit after cleanup
    loop = asyncio.get_running_loop()
    loop.stop()
    sys.exit(0)

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
        arbitrum_pipeline = ArbitrumPipeline(sql_database, mongodb_database)
        polygon_pipeline = PolygonChainPipeline(sql_database, mongodb_database)
        optimism_pipeline = OptimismChainPipeline(sql_database, mongodb_database)
        avalanche_pipeline = AvalancheChainPipeline(sql_database, mongodb_database)
        #polygonzk_pipeline = PolygonZKPipeline(sql_database, mongodb_database)
        #mantle_pipeline = MantlePipeline(sql_database, mongodb_database)
        #linea_pipeline = LineaPipeline(sql_database, mongodb_database)
        #zksync_pipeline = ZkSyncPipeline(sql_database, mongodb_database)


        # Add pipelines to active list
        active_pipelines.extend([
            ethereum_pipeline,
            bnb_pipeline,
            base_pipeline,
            bitcoin_pipeline,
            xrp_pipeline,
            arbitrum_pipeline,
            polygon_pipeline,
            optimism_pipeline,
            avalanche_pipeline,
            solana_pipeline,
            #polygonzk_pipeline,
            #mantle_pipeline,
            #linea_pipeline,
            #zksync_pipeline

        ])

        duration = 100000

        # Run all pipelines concurrently
        try:
            await asyncio.gather(
                ethereum_pipeline.run(duration=duration),
                #bnb_pipeline.run(duration=duration),
                #base_pipeline.run(duration=duration),
                #bitcoin_pipeline.run(duration=duration),
                #solana_pipeline.run(duration=1200),
                #xrp_pipeline.run(duration=duration),
                #arbitrum_pipeline.run(duration=duration),
                #polygon_pipeline.run(duration=duration),
                #optimism_pipeline.run(duration=duration),
                #avalanche_pipeline.run(duration=duration),
                #polygonzk_pipeline.run(duration=duration),
                #mantle_pipeline.run(duration=duration),
                #linea_pipeline.run(duration=duration),
                #zksync_pipeline.run(duration=duration)

            )
        finally:
            
            # Ensure cleanup happens even if gather fails
            await cleanup(active_pipelines)
            
    except Exception as e:
        # Ensure cleanup happens on error
        await cleanup(active_pipelines)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Setup signal handlers in a cross-platform way
    if sys.platform == 'win32':
        for s in (signal.SIGTERM, signal.SIGINT):
            signal.signal(s, lambda s, f: asyncio.create_task(signal_handler(s, f)))
    else:
        # Unix-like systems can use loop.add_signal_handler
        for s in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                s, lambda: asyncio.create_task(signal_handler(s, None))
            )
    
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("KeyboardInterrupt received")
        loop.run_until_complete(cleanup(active_pipelines))
    finally:
        loop.close()
