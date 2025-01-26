import asyncio
from typing import List
from database import SQLDatabase, MongoDatabase
from chains import (
    EthereumProcessor, BaseChainProcessor, BNBProcessor,
    EthereumQuerier, BaseChainQuerier, BNBQuerier, ArbitrumProcessor, ArbitrumQuerier
)
import logging

logging.basicConfig(level=logging.INFO)

async def process_chain_swaps(processor, swaps: List[tuple]):
    """Process swaps for a specific chain"""
    tasks = []
    for swap_tuple in swaps:
        try:
            contract_address = swap_tuple[0]  # swap_tuple format is (contract_address,)
            tasks.append(processor.process_contract(contract_address))
        except Exception as e:
            logging.error(f"Error processing swap {contract_address}: {e}")
    
    if tasks:
        await asyncio.gather(*tasks)

async def process_batch(sql_database, eth_processor, base_processor, bnb_processor, arbitrum_processor, last_address=None):
    """Process a batch of swaps"""
    query = """
        SELECT contract_address, network 
        FROM evm_swap 
        WHERE network IN ('Ethereum', 'Base', 'BNB', 'Arbitrum')
        AND contract_address > %s
        ORDER BY contract_address ASC
        LIMIT 1000
    """
    
    cursor = sql_database.conn.cursor()
    try:
        cursor.execute(query, (last_address if last_address else '',))
        all_swaps = cursor.fetchall()
    finally:
        cursor.close()
    
    if not all_swaps:
        return None  # No more swaps to process
    
    # Separate swaps by network
    eth_swaps = [(t[0],) for t in all_swaps if t[1] == 'Ethereum']
    base_swaps = [(t[0],) for t in all_swaps if t[1] == 'Base']
    bnb_swaps = [(t[0],) for t in all_swaps if t[1] == 'BNB']
    arbitrum_swaps = [(t[0],) for t in all_swaps if t[1] == 'Arbitrum']

    # Process all chains concurrently
    tasks = []
    if eth_swaps:
        tasks.append(process_chain_swaps(eth_processor, eth_swaps))
    if base_swaps:
        tasks.append(process_chain_swaps(base_processor, base_swaps))
    if bnb_swaps:
        tasks.append(process_chain_swaps(bnb_processor, bnb_swaps))
    if arbitrum_swaps:
        tasks.append(process_chain_swaps(arbitrum_processor, arbitrum_swaps))
    
    # Wait for all chains to complete processing
    if tasks:
        await asyncio.gather(*tasks)
    
    # Return the highest contract_address from this batch for next iteration
    return max(t[0] for t in all_swaps)

async def main():
    # Initialize databases and queriers
    sql_database = SQLDatabase()
    mongodb_database = MongoDatabase()
    
    # Initialize queriers and processors for each chain
    eth_querier = EthereumQuerier()
    base_querier = BaseChainQuerier()
    bnb_querier = BNBQuerier()
    arbitrum_querier = ArbitrumQuerier()

    eth_processor = EthereumProcessor(sql_database, mongodb_database, eth_querier)
    base_processor = BaseChainProcessor(sql_database, mongodb_database, base_querier)
    bnb_processor = BNBProcessor(sql_database, mongodb_database, bnb_querier)
    arbitrum_processor = ArbitrumProcessor(sql_database, mongodb_database, arbitrum_querier)

    # Process batches until no more swaps
    last_address = None
    batch_count = 0
    while True:
        last_address = await process_batch(
            sql_database,
            eth_processor,
            base_processor,
            bnb_processor,
            arbitrum_processor,
            last_address
        )
        
        if last_address is None:
            break
        
        batch_count += 1
        logging.info(f"Completed batch {batch_count}. Last address processed: {last_address}")

if __name__ == "__main__":
    asyncio.run(main())