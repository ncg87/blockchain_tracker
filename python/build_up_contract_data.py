from database import SQLDatabase, MongoDatabase
from chains import BaseChainProcessor, EthereumProcessor, BNBProcessor
from chains import BaseChainQuerier, EthereumQuerier, BNBQuerier
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import json
import logging

logging.basicConfig(level=logging.INFO)

sql_db = SQLDatabase()
mongo_db = MongoDatabase()

base_querier = BaseChainQuerier()
eth_querier = EthereumQuerier()
bnb_querier = BNBQuerier()

query = "SELECT * FROM evm_contract_abis WHERE network = 'Base'"
sql_db.cursor.execute(query)
base_contract_abis = sql_db.cursor.fetchall()

query = "SELECT * FROM evm_contract_abis WHERE network = 'Ethereum'"
sql_db.cursor.execute(query)
eth_contract_abis = sql_db.cursor.fetchall()

query = "SELECT * FROM evm_contract_abis WHERE network = 'BNB'"
sql_db.cursor.execute(query)
bnb_contract_abis = sql_db.cursor.fetchall()

bnb_processor = BNBProcessor(sql_db, mongo_db, bnb_querier)
eth_processor = EthereumProcessor(sql_db, mongo_db, eth_querier)
base_processor = BaseChainProcessor(sql_db, mongo_db, base_querier)

async def process_all_contracts(processor, contract_abis):
    # Create a thread pool - adjust max_workers as needed
    thread_pool = ThreadPoolExecutor(max_workers=10)
    loop = asyncio.get_event_loop()
    
    # Create tasks that run in thread pool
    tasks = [
        loop.run_in_executor(
            thread_pool,
            partial(asyncio.run, processor._process_contract(contract[1], json.loads(contract[2], update=True)))
        )
        for contract in contract_abis
    ]
    
    # Gather results
    results = await asyncio.gather(*tasks)
    contract_info = [result for result in results if result]
    for result in contract_info:
        print(result)
    
    thread_pool.shutdown()
    return contract_info

async def main():
    # Create a thread pool for all processors
    thread_pool = ThreadPoolExecutor(max_workers=30)  # Increased for 3 chains
    loop = asyncio.get_event_loop()
    
    # Process all chains in parallel
    tasks = []
    processor_data = [
        (base_processor, base_contract_abis),
        (eth_processor, eth_contract_abis),
        (bnb_processor, bnb_contract_abis)
    ]
    
    for processor, contract_abis in processor_data:
        chain_tasks = [
            loop.run_in_executor(
                thread_pool,
                partial(asyncio.run, processor._process_contract(contract[1], json.loads(contract[2])))
            )
            for contract in contract_abis
        ]
        tasks.extend(chain_tasks)
    
    # Gather all results
    results = await asyncio.gather(*tasks)
    contract_info = [result for result in results if result]
    for result in contract_info:
        print(result)
    
    thread_pool.shutdown()
    return contract_info

if __name__ == "__main__":
    asyncio.run(main())
