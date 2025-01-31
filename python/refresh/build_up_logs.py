import asyncio
from typing import List
from config import Settings
from chains import (
    EthereumQuerier, EthereumProcessor, EthereumPipeline,
    BaseChainQuerier, BaseChainProcessor, BaseChainPipeline,
    BNBQuerier, BNBProcessor, BNBPipeline
)
from database import SQLDatabase, MongoDatabase
import logging

logging.basicConfig(level=logging.INFO)

async def process_chain_blocks(processor, blocks: List[tuple]):
    """Process blocks for a specific chain"""
    tasks = []
    for block_tuple in blocks:
        try:
            # Convert tuple to the format process_block expects
            # block_tuple format is (network, block_number, timestamp)
            block_dict = {
                'number': block_tuple[1],  # block_number
                'timestamp': block_tuple[2],  # timestamp
                'hash': None,  # Add other required fields
                'parentHash': None
            }
            tasks.append(processor.process_block(block_dict))
        except Exception as e:
            logging.error(f"Error processing block {block_tuple[1]}: {e}")
    
    if tasks:
        await asyncio.gather(*tasks)

async def process_batch(sql_database, eth_processor, base_processor, bnb_processor, last_block=None):
    """Process a batch of blocks"""
    # Query for next batch
    query = """
        SELECT network, block_number, timestamp 
        FROM blocks 
        WHERE network IN ('Ethereum', 'Base', 'BNB')
        AND block_number < %s
        ORDER BY block_number DESC
        LIMIT 1000
    """
    
    # Create a new cursor for this batch
    cursor = sql_database.conn.cursor()
    try:
        cursor.execute(query, (last_block if last_block else float('inf'),))
        all_blocks = cursor.fetchall()
    finally:
        cursor.close()
    
    if not all_blocks:
        return None  # No more blocks to process
    
    # Separate blocks by network using indices
    eth_blocks = [b for b in all_blocks if b[0] == 'Ethereum']
    base_blocks = [b for b in all_blocks if b[0] == 'Base']
    bnb_blocks = [b for b in all_blocks if b[0] == 'BNB']
    
    # Process all chains concurrently
    tasks = []
    if eth_blocks:
        tasks.append(process_chain_blocks(eth_processor, eth_blocks))
    if base_blocks:
        tasks.append(process_chain_blocks(base_processor, base_blocks))
    if bnb_blocks:
        tasks.append(process_chain_blocks(bnb_processor, bnb_blocks))
    
    # Wait for all chains to complete processing
    if tasks:
        await asyncio.gather(*tasks)
    
    # Return the lowest block number from this batch for next iteration
    return min(b[1] for b in all_blocks)  # b[1] is block_number

async def main():
    # Initialize databases and queriers
    sql_database = SQLDatabase()
    mongodb_database = MongoDatabase()
    
    # Initialize processors for each chain
    eth_querier = EthereumQuerier()
    base_querier = BaseChainQuerier()
    bnb_querier = BNBQuerier()
    
    eth_processor = EthereumProcessor(sql_database, mongodb_database, eth_querier)
    base_processor = BaseChainProcessor(sql_database, mongodb_database, base_querier)
    bnb_processor = BNBProcessor(sql_database, mongodb_database, bnb_querier)
    
    # Process batches until no more blocks
    last_block = None
    batch_count = 0
    while True:
        last_block = await process_batch(
            sql_database, 
            eth_processor, 
            base_processor, 
            bnb_processor, 
            last_block
        )
        
        if last_block is None:
            break
            
        batch_count += 1
        logging.info(f"Completed batch {batch_count}. Last block processed: {last_block}")

if __name__ == "__main__":
    asyncio.run(main())