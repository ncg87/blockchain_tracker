from web3 import Web3
from config import Settings
from database import MongoDatabase, SQLDatabase, DatabaseOperator
import json
import csv
import asyncio
import os
import pickle
from chains import BaseChainQuerier

# Initialize connections
querier = BaseChainQuerier()
w3 = Web3(Web3.HTTPProvider(Settings.BASE_ENDPOINT))
db_operator = DatabaseOperator(SQLDatabase(), MongoDatabase())

# Equalizer factory address
FACTORY_ADDRESS = "0xEd8db60aCc29e14bC867a497D94ca6e3CeB5eC04"

# Get current block and calculate block from start
current_block = w3.eth.block_number
from_block = 0  # Start from beginning
print(f"Querying from block {from_block} to {current_block}")

# Checkpoint file to save progress
CHECKPOINT_FILE = "equalizer_checkpoint.pkl"
CSV_FILE = os.path.join(os.getcwd(), "FULL_equalizer_pools.csv")
print(f"CSV will be saved to: {CSV_FILE}")

class SimpleQuerier:
    def __init__(self, web3_instance):
        self.w3 = web3_instance
    
    def get_transaction_receipt(self, tx_hash):
        return self.w3.eth.get_transaction_receipt(tx_hash)
    
    def get_contract(self, address, abi):
        return self.w3.eth.contract(address=address, abi=abi)
    
    def get_block_logs(self, block_number):
        return self.w3.eth.get_logs({'fromBlock': block_number, 'toBlock': block_number})
    
    def get_transaction(self, tx_hash):
        return self.w3.eth.get_transaction(tx_hash)

# Create a simple querier instance
simple_querier = SimpleQuerier(w3)

def get_factory_contract(address):
    # Get the abi for the actual contract and call it on the proxy address
    abi = db_operator.sql.query.evm.query_contract_abi('base', '0x8104bEaE44f19f0cBDa1985Ac983a107115A417F')
    if not abi:
        print(f"ABI not found for address: {address}")
        return None
    
    contract = w3.eth.contract(address=address, abi=json.loads(abi['abi']))
    return contract

def get_pool_contract(pool_address):
    abi_data = db_operator.sql.query.evm.query_contract_abi('base', pool_address)
    if not abi_data:
        print(f"ABI not found for pool address: {pool_address}")
        return None
    contract = w3.eth.contract(address=pool_address, abi=json.loads(abi_data['abi']))
    return contract

def save_to_csv(data, first_write=False):
    mode = 'w' if first_write else 'a'
    with open(CSV_FILE, mode, newline='') as f:
        writer = csv.writer(f)
        if first_write:
            writer.writerow([
                'Pool Address', 'Token0', 'Token1', 'Is Stable', 'Fee', 'Block Number',
            ])
        writer.writerows(data)
    print(f"Saved {len(data)} rows to CSV")

def save_checkpoint(last_processed_chunk, processed_pairs):
    with open(CHECKPOINT_FILE, 'wb') as f:
        pickle.dump((last_processed_chunk, processed_pairs), f)
    print(f"Checkpoint saved: processed {len(processed_pairs)} pairs")

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'rb') as f:
            return pickle.load(f)
    return 0, set()

async def process_equalizer_pairs():
    # Get factory contract first
    factory_contract = get_factory_contract(FACTORY_ADDRESS)
    if not factory_contract:
        print("Failed to get factory contract. Exiting.")
        return
    
    # Verify this is the correct factory by checking allPairsLength
    try:
        total_pairs = factory_contract.functions.allPairsLength().call()
        print(f"Total pairs found: {total_pairs}")
    except Exception as e:
        print(f"Error verifying factory contract: {e}")
        return
    
    # Load checkpoint if exists
    chunk_counter, processed_pairs = load_checkpoint()
    
    # Define the PairCreated event signature
    pair_created_event = factory_contract.events.PairCreated()
    
    # Process in chunks
    chunk_size = 1000
    first_write = not os.path.exists(CSV_FILE)
    temporary_data = []
    
    # Get all PairCreated events
    print(f"Getting PairCreated events from block {from_block} to {current_block}...")
    
    # Process in chunks to avoid timeouts
    for chunk_start in range(from_block + chunk_counter * chunk_size, current_block, chunk_size):
        chunk_end = min(chunk_start + chunk_size, current_block)
        chunk_counter += 1
        
        print(f"Processing chunk {chunk_counter}: blocks {chunk_start} to {chunk_end}")
        
        try:
            # Get PairCreated events in this block range
            events = pair_created_event.get_logs(from_block=chunk_start, to_block=chunk_end)
            print(f"  Found {len(events)} PairCreated events in this chunk")
            
            for event in events:
                try:
                    # Extract data from event
                    token0 = event['args']['token0']
                    token1 = event['args']['token1']
                    is_stable_from_event = event['args']['stable']
                    pool_address = event['args']['pair']
                    
                    # Skip if already processed
                    if pool_address in processed_pairs:
                        print(f"  Pool {pool_address} already processed, skipping")
                        continue
                    
                    print(f"  Processing pool {pool_address}")
                    
                    # Get and save the ABI
                    try:
                        abi = await querier.get_contract_abi(pool_address)
                        if abi is None:
                            print(f"  No ABI found for pool {pool_address}, using a generic pool ABI")
                            # Use a generic pool ABI or get it from a known pool
                            generic_pool_abi = db_operator.sql.query.evm.query_contract_abi('base', '0x7bDc79D35465DB767F0B23ccA23738F652AE187b')
                            if generic_pool_abi:
                                abi = generic_pool_abi['abi']
                            else:
                                # Fallback to a minimal ABI with just the functions we need
                                abi = json.dumps([
                                    {"inputs": [], "name": "stable", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "view", "type": "function"},
                                    {"inputs": [], "name": "token0", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
                                    {"inputs": [], "name": "token1", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"}
                                ])
                        
                        # Only save the ABI if it's not None
                        if abi:
                            db_operator.sql.insert.evm.contract_abi('base', pool_address, abi)
                    except Exception as e:
                        print(f"  Error getting ABI for pool {pool_address}: {e}")
                        # Fallback to a minimal ABI with just the functions we need
                        abi = json.dumps([
                            {"inputs": [], "name": "stable", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "view", "type": "function"},
                            {"inputs": [], "name": "token0", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
                            {"inputs": [], "name": "token1", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"}
                        ])
                    
                    # Get pool details
                    try:
                        pool_contract = w3.eth.contract(address=pool_address, abi=json.loads(abi) if isinstance(abi, str) else abi)
                        is_stable = pool_contract.functions.stable().call()
                        fee = factory_contract.functions.getRealFee(pool_address).call()
                    except Exception as e:
                        print(f"  Error getting pool details: {e}")
                        # Use the stable value from the event if we can't get it from the contract
                        is_stable = is_stable_from_event
                        try:
                            fee = factory_contract.functions.getRealFee(pool_address, is_stable).call()
                        except Exception as e:
                            print(f"  Error getting fee: {e}")
                            fee = "Unknown"
                    
                    # Add to temporary data
                    temporary_data.append([
                        pool_address, token0, token1, is_stable, fee, event['blockNumber'],
                    ])
                    processed_pairs.add(pool_address)
                    
                    # Sleep briefly between requests
                    await asyncio.sleep(0.2)
                    
                except Exception as e:
                    print(f"  Error processing pool {pool_address}: {e}")
                    continue
            
            # Save progress every 20 chunks
            if chunk_counter % 20 == 0:
                save_to_csv(temporary_data, first_write if first_write else False)
                first_write = False
                save_checkpoint(chunk_counter, processed_pairs)
                temporary_data = []  # Clear temporary data after saving
        
        except Exception as e:
            print(f"Error processing chunk {chunk_counter}: {e}")
            # Save progress on error
            if temporary_data:
                save_to_csv(temporary_data, first_write if first_write else False)
                first_write = False
                save_checkpoint(chunk_counter, processed_pairs)
                temporary_data = []
    
    # Save any remaining data
    if temporary_data:
        save_to_csv(temporary_data, first_write if first_write else False)
        save_checkpoint(chunk_counter, processed_pairs)
    
    print("Finished processing all Equalizer pools")

if __name__ == "__main__":
    asyncio.run(process_equalizer_pairs()) 