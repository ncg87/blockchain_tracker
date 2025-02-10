from database import SQLDatabase, MongoDatabase, DatabaseOperator
from chains import *
import asyncio
import json
import aiofiles
import os
from typing import Dict, List, Set
import logging
import time
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
PROGRESS_FILE = "factory_progress.json"
BATCH_SIZE = 5  # Number of concurrent factory processing tasks

sql_db = SQLDatabase()
mongo_db = MongoDatabase()

db_operator = DatabaseOperator(sql_db, mongo_db)

query = """SELECT DISTINCT factory_address, chain, name
FROM evm_contract_to_factory
ORDER BY chain, factory_address;"""

sql_db.cursor.execute(query)
factories = sql_db.cursor.fetchall()

chain_to_querier = {
    "ethereum": EthereumQuerier(),
    #"polygon": PolygonChainQuerier(),
    #"arbitrum": ArbitrumQuerier(),
    #"optimism": OptimismChainQuerier(),
    #"base": BaseChainQuerier(),
    #"avalanche": AvalancheChainQuerier(),
    #"bnb": BNBQuerier(),
    # "linea": LineaQuerier(),
    # "mantle": MantleQuerier(),
    # "zksync": ZkSyncQuerier(),
    # "polygonzk": PolygonZKQuerier(),
}

chain_to_processor = {
    "ethereum": EthereumProcessor(sql_db, mongo_db, chain_to_querier["ethereum"]),
    #"polygon": PolygonChainProcessor(sql_db, mongo_db, chain_to_querier["polygon"]),
    #"arbitrum": ArbitrumProcessor(sql_db, mongo_db, chain_to_querier["arbitrum"]),
    #"optimism": OptimismChainProcessor(sql_db, mongo_db, chain_to_querier["optimism"]),
    #"base": BaseChainProcessor(sql_db, mongo_db, chain_to_querier["base"]),
    #"avalanche": AvalancheChainProcessor(sql_db, mongo_db, chain_to_querier["avalanche"]),
    #"bnb": BNBProcessor(sql_db, mongo_db, chain_to_querier["bnb"]),
    # "linea": LineaProcessor(sql_db, mongo_db, chain_to_querier["linea"]),
    # "mantle": MantleProcessor(sql_db, mongo_db, chain_to_querier["mantle"]),
    # "zksync": ZkSyncProcessor(sql_db, mongo_db, chain_to_querier["zksync"]),
    # "polygonzk": PolygonZKProcessor(sql_db, mongo_db, chain_to_querier["polygonzk"]),
}

chain_to_max_block = {
    "ethereum":  21800000,
    #"polygon":   67500000,
    #"arbitrum":  302100000,
    #"optimism":  131500000,
    #"base":      25900000,
    #"avalanche": 5680000,
    #"bnb":       46300000,
    #"linea":     46300000,
    #"mantle":    75100000,
    #"zksync":    55000000,
    #"polygonzk": 19600000,
}

chain = 'ethereum'


class FactoryProcessor:
    def __init__(self):
        self.sql_db = SQLDatabase()
        self.mongo_db = MongoDatabase()
        self.db_operator = DatabaseOperator(self.sql_db, self.mongo_db)
        self.progress = self.load_progress()
        
    def load_progress(self) -> Dict:
        """Load progress from file or create new progress tracker"""
        if os.path.exists(PROGRESS_FILE):
            try:
                with open(PROGRESS_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading progress file: {e}")
        return {
            "completed": {},
            "in_progress": {},
            "failed": {}
        }

    async def save_progress(self):
        """Save progress to file asynchronously"""
        try:
            async with aiofiles.open(PROGRESS_FILE, 'w') as f:
                await f.write(json.dumps(self.progress, indent=2))
        except Exception as e:
            logger.error(f"Error saving progress: {e}")

    async def process_pairs(self, pairs: list, processor, factory_key: str):
        """Process a batch of pairs concurrently"""
        PAIR_BATCH_SIZE = 10  # Number of pairs to process simultaneously
        
        for i in range(0, len(pairs), PAIR_BATCH_SIZE):
            batch = pairs[i:i + PAIR_BATCH_SIZE]
            tasks = []
            
            for pair in batch:
                async def process_single_pair(pair_address):
                    while True:
                        try:
                            await processor.log_processor.process_contract(pair_address)
                            self.db_operator.sql.insert.evm.contract_to_factory(chain, pair_address, factory_key)
                            return True
                        except Exception as e:

                            if "connection" in str(e).lower():
                                logger.warning(f"Connection issue, retrying in 30s: {e}")
                                await asyncio.sleep(30)
                                continue
                            logger.error(f"Error processing pair {pair_address}: {e}")
                            return False
                
                tasks.append(process_single_pair(pair['address']))
            
            # Process batch of pairs concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Update progress
            self.progress["in_progress"][factory_key]["pairs_processed"] = i + len(batch)
            await self.save_progress()
            
            # Optional: Add a small delay between batches to prevent rate limiting
            await asyncio.sleep(1)

    async def process_factory(self, factory: tuple, querier):
        """Process a single factory and its pairs"""
        chain, address = factory['chain'], factory['factory_address']
        factory_key = f"{chain}:{address}"

        try:
            if factory_key in self.progress["completed"]:
                logger.info(f"Skipping completed factory {factory_key}")
                return

            self.progress["in_progress"][factory_key] = {
                "start_time": time.time(),
                "pairs_processed": 0
            }
            await self.save_progress()

            abi = await querier.get_contract_abi(address)
            if not abi:
                raise Exception(f"Failed to get ABI for {address}")

            # Check if PairCreated event exists in ABI
            has_pair_created = any(
                item.get('type') == 'event' and 
                item.get('name') == 'PairCreated' 
                for item in abi
            )
            
            if not has_pair_created:
                logger.info(f"Skipping factory {factory_key} - No PairCreated event in ABI")
                self.progress["completed"][factory_key] = {
                    "total_pairs": 0,
                    "completion_time": time.time(),
                    "reason": "No PairCreated event"
                }
                del self.progress["in_progress"][factory_key]
                await self.save_progress()
                return

            contract = querier.get_contract(address, abi)
            pairs = []
            
            # Collect all pairs first
            max_block = chain_to_max_block[chain]
            for i in range(0, max_block, 10000):
                max_retries = 3  # Maximum number of retry attempts
                retry_count = 0
                
                while retry_count < max_retries:
                    try:
                        filter = contract.events.PairCreated().create_filter(
                            from_block=i, 
                            to_block=min(i + 10000, max_block)
                        )
                        pair_blocks = filter.get_all_entries()
                        if pair_blocks:
                            pairs.extend(pair_blocks)
                        break  # Success - exit retry loop
                    except Exception as e:
                        retry_count += 1
                        if "connection" in str(e).lower() and retry_count < max_retries:
                            logger.warning(f"Connection issue on block range {i}-{i+10000}, attempt {retry_count}/{max_retries}: {e}")
                            await asyncio.sleep(30)
                            continue
                        if retry_count == max_retries:
                            logger.error(f"Max retries reached for block range {i}-{i+10000}: {e}")
                        raise

                logger.info(f"Processed block range {i}-{min(i + 10000, max_block)} for factory {factory_key}")

            # Process pairs concurrently
            processor = chain_to_processor[chain]
            await self.process_pairs(pairs, processor, factory_key)

            # Mark as completed
            self.progress["completed"][factory_key] = {
                "total_pairs": len(pairs),
                "completion_time": time.time()
            }
            del self.progress["in_progress"][factory_key]
            await self.save_progress()

        except Exception as e:
            logger.error(f"Error processing factory {factory_key}: {e}")
            self.progress["failed"][factory_key] = str(e)
            if factory_key in self.progress["in_progress"]:
                del self.progress["in_progress"][factory_key]
            await self.save_progress()

    async def process_all_factories(self):
        """Process all factories with concurrency control"""
        query = """SELECT DISTINCT factory_address, chain, name
                  FROM evm_contract_to_factory
                  WHERE chain = 'ethereum'
                  ORDER BY chain, factory_address;"""
        
        self.sql_db.cursor.execute(query)
        factories = self.sql_db.cursor.fetchall()
        
        # Process Ethereum factories
        logger.info(f"Processing {len(factories)} factories for ethereum")
        querier = chain_to_querier["ethereum"]
        
        # Process factories in batches
        for i in range(0, len(factories), BATCH_SIZE):
            batch = factories[i:i + BATCH_SIZE]
            tasks = [self.process_factory(factory, querier) for factory in batch]
            await asyncio.gather(*tasks)

async def main():
    processor = FactoryProcessor()
    await processor.process_all_factories()

if __name__ == "__main__":
    asyncio.run(main())