from web3 import Web3
from config import Settings
from database import MongoDatabase, SQLDatabase, DatabaseOperator
import json
import csv
from chains import BaseChainQuerier
import asyncio
import os
import pickle

# Initialize connections
querier = BaseChainQuerier()
w3 = Web3(Web3.HTTPProvider(Settings.BASE_ENDPOINT))
db_operator = DatabaseOperator(SQLDatabase(), MongoDatabase())

# Aerodrome factory address
FACTORY_ADDRESS = "0x420DD381b31aEf6683db6B902084cB0FFECe40Da"

# Get current block and calculate block from 1 year ago
# Base has roughly 2 second block times
BLOCKS_PER_DAY = 24 * 60 * 60 // 2  # ~43200 blocks per day
current_block = w3.eth.block_number
from_block = 0  # Approximately 1 year
print(f"Querying from block {from_block} to {current_block}")

# Checkpoint file to save progress
CHECKPOINT_FILE = "aerodrome_checkpoint.pkl"
CSV_FILE = os.path.join(os.getcwd(), "FULL_aerodrome_pools.csv")
print(f"CSV will be saved to: {CSV_FILE}")

# Get factory contract
def get_factory_contract(address):
    abi = db_operator.sql.query.evm.query_contract_abi('base', address)
    if not abi:
        print(f"ABI not found for address: {address}")
        return None
    contract = w3.eth.contract(address=address, abi=json.loads(abi['abi']))
    return contract

# Get pool contract
def get_pool_contract(pool_address):
    abi_data = db_operator.sql.query.evm.query_contract_abi('base', pool_address)
    abi = abi_data.get('abi', None)
    if not abi:
        abi = """        
        minimal_factory_abi = json.dumps([
            {
                "inputs": [{"internalType": "address", "name": "pool", "type": "address"},
                           {"internalType": "bool", "name": "stable", "type": "bool"}],
                "name": "getFee",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "anonymous": False,
                "inputs": [{"indexed": True, "internalType": "address", "name": "token0", "type": "address"},
                           {"indexed": True, "internalType": "address", "name": "token1", "type": "address"},
                           {"indexed": True, "internalType": "bool", "name": "stable", "type": "bool"},
                           {"indexed": False, "internalType": "address", "name": "pool", "type": "address"},
                           {"indexed": False, "internalType": "uint256", "name": "", "type": "uint256"}],
                "name": "PoolCreated",
                "type": "event"
            },
            {
                "inputs": [],
                "name": "allPoolsLength",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }
        ])
        """
    contract = w3.eth.contract(address=pool_address, abi=json.loads(abi))
    return contract

# Save data to CSV with improved error handling
def save_to_csv(data, first_write=False):
    try:
        # Determine if this is the first write
        file_exists = os.path.exists(CSV_FILE)
        first_write = first_write or not file_exists
        
        mode = 'w' if first_write else 'a'
        print(f"Opening CSV file in {'write' if first_write else 'append'} mode")
        
        with open("FULL_aerodrome_pools.csv", mode, newline='') as csvfile:
            writer = csv.writer(csvfile)
            if first_write:
                writer.writerow(['pool_address', 'token0', 'token1', 'is_stable', 'fee', 'creation_block'])
                print("Wrote CSV header")
            
            for row in data:
                writer.writerow(row)
            
            # Force flush to disk
            csvfile.flush()
            os.fsync(csvfile.fileno())
        
        print(f"Successfully saved {len(data)} entries to CSV at {CSV_FILE}")
        
        # Verify the file was created
        if os.path.exists(CSV_FILE):
            print(f"CSV file exists at {CSV_FILE} with size {os.path.getsize(CSV_FILE)} bytes")
        else:
            print(f"WARNING: CSV file was not found after writing!")
    
    except Exception as e:
        print(f"ERROR saving to CSV: {e}")
        # Try alternate approach if the first one fails
        try:
            print("Trying alternate CSV save method...")
            with open(CSV_FILE, 'w' if first_write else 'a', newline='') as f:
                for row in data:
                    if first_write:
                        f.write("pool_address,token0,token1,is_stable,fee,creation_block\n")
                        first_write = False
                    f.write(",".join(str(item) for item in row) + "\n")
                f.flush()
            print("Alternate method completed")
        except Exception as e2:
            print(f"ERROR with alternate CSV save method: {e2}")

# Save checkpoint
def save_checkpoint(last_processed_chunk, processed_pairs):
    with open(CHECKPOINT_FILE, 'wb') as f:
        pickle.dump({'last_chunk': last_processed_chunk, 'processed_pairs': processed_pairs}, f)
    print(f"Saved checkpoint at chunk {last_processed_chunk}")

# Load checkpoint
def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'rb') as f:
            return pickle.load(f)
    return {'last_chunk': -1, 'processed_pairs': set()}

async def process_aerodrome_pairs():
    # Get factory contract first
    factory_abi = await querier.get_contract_abi(FACTORY_ADDRESS)
    db_operator.sql.insert.evm.contract_abi('base', FACTORY_ADDRESS, factory_abi)
    factory_contract = get_factory_contract(FACTORY_ADDRESS)
    
    if not factory_contract:
        print(f"Could not get factory contract for {FACTORY_ADDRESS}")
        return
    
    # Load checkpoint if exists
    checkpoint = load_checkpoint()
    last_processed_chunk = checkpoint['last_chunk']
    processed_pairs = checkpoint['processed_pairs']
    
    # Force creation of CSV file with header at the beginning
    if not os.path.exists(CSV_FILE):
        print(f"Creating new CSV file at {CSV_FILE}")
        save_to_csv([], first_write=True)
    else:
        print(f"CSV file already exists at {CSV_FILE}")
    
    # Query in chunks to avoid RPC limitations
    CHUNK_SIZE = 10000
    all_pairs = []
    chunk_counter = 0
    temporary_data = []
    
    # Process chunks
    print(f"Starting from chunk {last_processed_chunk + 1}")
    for chunk_start in range(from_block, current_block, CHUNK_SIZE):
        chunk_end = min(chunk_start + CHUNK_SIZE, current_block)
        chunk_counter += 1
        
        # Skip already processed chunks
        if chunk_counter <= last_processed_chunk:
            print(f"Skipping already processed chunk {chunk_counter}")
            continue
        
        print(f"Querying chunk {chunk_counter}: blocks {chunk_start} to {chunk_end}")
        
        try:
            # Look for PoolCreated events
            pair_filter = factory_contract.events.PoolCreated.create_filter(
                from_block=chunk_start,
                to_block=chunk_end
            )
            events = pair_filter.get_all_entries()
            print(f"  Found {len(events)} pools in this chunk")
            
            # Process and store events from this chunk
            for event in events:
                pool_address = event.args.pool
                
                # Skip already processed pairs
                if pool_address in processed_pairs:
                    print(f"  Skipping already processed pool: {pool_address}")
                    continue
                
                try:
                    token0 = event.args.token0
                    token1 = event.args.token1
                    
                    print(f"  Processing pool: {pool_address}")
                    
                    # Get and save the ABI
                    abi = await querier.get_contract_abi(pool_address)
                    db_operator.sql.insert.evm.contract_abi('base', pool_address, abi)
                    
                    # Get pool details
                    pool_contract = get_pool_contract(pool_address)
                    is_stable = pool_contract.functions.stable().call()
                    fee = factory_contract.functions.getFee(pool_address, is_stable).call()
                    
                    # Add to temporary data
                    temporary_data.append([pool_address, token0, token1, is_stable, fee, event.blockNumber])
                    processed_pairs.add(pool_address)
                    
                    # Sleep briefly between requests
                    await asyncio.sleep(0.2)
                    
                except Exception as e:
                    print(f"  Error processing pool {pool_address}: {e}")
                    continue
            
            # Save progress every 20 chunks
            if chunk_counter % 20 == 0:
                save_to_csv(temporary_data)
                save_checkpoint(chunk_counter, processed_pairs)
                temporary_data = []  # Clear temporary data after saving
            
            # Sleep briefly to avoid overwhelming the RPC provider
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"  Error querying chunk {chunk_counter}: {e}")
            await asyncio.sleep(5)  # Wait longer on error
            continue
    
    # Save any remaining data
    if temporary_data:
        save_to_csv(temporary_data)
        save_checkpoint(chunk_counter, processed_pairs)
    
    print(f"Total pools processed: {len(processed_pairs)}")

if __name__ == "__main__":
    asyncio.run(process_aerodrome_pairs())
