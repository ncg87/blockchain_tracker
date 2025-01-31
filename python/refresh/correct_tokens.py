import asyncio
from typing import List
from database import SQLDatabase, MongoDatabase
from chains import (
    EthereumProcessor, BaseChainProcessor, BNBProcessor,
    EthereumQuerier, BaseChainQuerier, BNBQuerier
)
import logging


logging.basicConfig(level=logging.INFO)

async def process_chain_tokens(processor, tokens: List[tuple]):
    """Process tokens for a specific chain"""
    tasks = []
    for token_tuple in tokens:
        try:
            contract_address = token_tuple[0]  # token_tuple format is (contract_address,)
            tasks.append(processor._process_token(contract_address))
        except Exception as e:
            logging.error(f"Error processing token {contract_address}: {e}")
    
    if tasks:
        await asyncio.gather(*tasks)

async def process_batch(sql_database, eth_processor, base_processor, bnb_processor, last_address=None):
    """Process a batch of tokens"""
    # Query for next batch of tokens
    query = """
        SELECT contract_address, network 
        FROM evm_token_info 
        WHERE network IN ('Ethereum', 'Base', 'BNB')
        AND contract_address > %s
        ORDER BY contract_address ASC
        LIMIT 1000
    """
    
    cursor = sql_database.conn.cursor()
    try:
        cursor.execute(query, (last_address if last_address else '',))
        all_tokens = cursor.fetchall()
    finally:
        cursor.close()
    
    if not all_tokens:
        return None  # No more tokens to process
    
    # Separate tokens by network
    eth_tokens = [(t[0],) for t in all_tokens if t[1] == 'Ethereum']
    base_tokens = [(t[0],) for t in all_tokens if t[1] == 'Base']
    bnb_tokens = [(t[0],) for t in all_tokens if t[1] == 'BNB']
    
    # Process all chains concurrently
    tasks = []
    if eth_tokens:
        tasks.append(process_chain_tokens(eth_processor, eth_tokens))
    if base_tokens:
        tasks.append(process_chain_tokens(base_processor, base_tokens))
    if bnb_tokens:
        tasks.append(process_chain_tokens(bnb_processor, bnb_tokens))
    
    # Wait for all chains to complete processing
    if tasks:
        await asyncio.gather(*tasks)
    
    # Return the highest contract_address from this batch for next iteration
    return max(t[0] for t in all_tokens)

async def main():
    # Initialize databases and queriers
    sql_database = SQLDatabase()
    mongodb_database = MongoDatabase()
    
    # Initialize queriers and processors for each chain
    eth_querier = EthereumQuerier()
    base_querier = BaseChainQuerier()
    bnb_querier = BNBQuerier()
    
    eth_processor = EthereumProcessor(sql_database, mongodb_database, eth_querier)
    base_processor = BaseChainProcessor(sql_database, mongodb_database, base_querier)
    bnb_processor = BNBProcessor(sql_database, mongodb_database, bnb_querier)
    
    # Process batches until no more tokens
    last_address = None
    batch_count = 0
    while True:
        last_address = await process_batch(
            sql_database,
            eth_processor,
            base_processor,
            bnb_processor,
            last_address
        )
        
        if last_address is None:
            break
        
        batch_count += 1
        logging.info(f"Completed batch {batch_count}. Last address processed: {last_address}")

if __name__ == "__main__":
    asyncio.run(main())