from web3 import Web3
import json
from datetime import datetime, timedelta
import pandas as pd
from config import Settings
import time
import asyncio
from chains.evm_models.evm_processor import LogProcessor
from chains.evm_models.evm_processor import EventProcessor
from database import DatabaseOperator, SQLDatabase, MongoDatabase

# Connect to Base network
# You'll need an RPC endpoint - use a service like Alchemy, Infura, QuickNode, etc.
RPC_URL = Settings.BASE_ENDPOINT
web3 = Web3(Web3.HTTPProvider(RPC_URL))

# Create a simple querier class to work with LogProcessor
class SimpleQuerier:
    def __init__(self, web3_instance):
        self.web3 = web3_instance
        
    def get_transaction_receipt(self, tx_hash):
        return self.web3.eth.get_transaction_receipt(tx_hash)
        
    def get_contract(self, address, abi):
        return self.web3.eth.contract(address=address, abi=abi)
        
    # Add any other methods that might be needed by LogProcessor
    def get_block_logs(self, block_number):
        return self.web3.eth.get_logs({'blockNumber': block_number})
        
    def get_transaction(self, tx_hash):
        return self.web3.eth.get_transaction(tx_hash)

# Aerodrome Factory ABI - include the minimum needed (at least the SetCustomFee event)
AERODROME_FACTORY_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "pool",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "fee",
                "type": "uint256"
            }
        ],
        "name": "SetCustomFee",
        "type": "event"
    }
    # Add other needed ABI elements here
]

# Initialize the database operator and processors
db_operator = DatabaseOperator(SQLDatabase(), MongoDatabase())
querier = SimpleQuerier(web3)

# Create a mock ABI object if LogProcessor expects one
abi = {"abi": json.dumps(AERODROME_FACTORY_ABI)}

log_processor = LogProcessor(db_operator, querier, "base")
event_processor = EventProcessor(db_operator, "base")

# Check connection
if not web3.is_connected():
    raise Exception("Failed to connect to Base network")

# Contract details
FACTORY_ADDRESS = "0x420DD381b31aEf6683db6B902084cB0FFECe40Da"  # Aerodrome pool factory

# The event signature for SetCustomFee event
EVENT_SIGNATURE = web3.keccak(text="SetCustomFee(address,uint256)").hex()

# Get current block
current_block = web3.eth.block_number
print(f"Current block: {current_block}")

# Blocks per hour - Base has roughly 2 second block times
BLOCKS_PER_HOUR = 60 * 60 // 2  # ~1800 blocks per hour
DAYS_TO_QUERY = 30
HOURS_PER_DAY = 24
TOTAL_HOURS = DAYS_TO_QUERY * HOURS_PER_DAY
chunk_size = BLOCKS_PER_HOUR  # Query one hour at a time

# Initialize results list
all_events = []

# Query logs in chunks
for hour in range(TOTAL_HOURS):
    to_block = current_block - (hour * BLOCKS_PER_HOUR)
    from_block = to_block - BLOCKS_PER_HOUR
    
    print(f"Querying hour {hour+1}/{TOTAL_HOURS}: blocks {from_block} to {to_block}")
    
    try:
        # Query the logs for this chunk
        events = web3.eth.get_logs({
            'address': FACTORY_ADDRESS,
            'fromBlock': from_block,
            'toBlock': to_block,
            'topics': [f"0x{EVENT_SIGNATURE}"]
        })
        
        print(f"  Found {len(events)} events in this chunk")
        all_events.extend(events)
        
        # Sleep briefly to avoid overwhelming the RPC provider
        time.sleep(0.5)
        
    except Exception as e:
        print(f"  Error querying chunk: {e}")
        # If we hit rate limits or other errors, wait longer before retry
        time.sleep(2)
        
        # Try to break the chunk into smaller pieces
        try:
            print(f"  Retrying with smaller chunks...")
            sub_chunk_size = BLOCKS_PER_HOUR // 4
            
            for i in range(4):
                sub_to_block = from_block + ((i+1) * sub_chunk_size)
                sub_from_block = from_block + (i * sub_chunk_size)
                
                if sub_to_block > to_block:
                    sub_to_block = to_block
                
                print(f"    Querying sub-chunk {i+1}/4: blocks {sub_from_block} to {sub_to_block}")
                
                sub_events = web3.eth.get_logs({
                    'address': FACTORY_ADDRESS,
                    'fromBlock': sub_from_block,
                    'toBlock': sub_to_block,
                    'topics': [EVENT_SIGNATURE]
                })
                
                print(f"      Found {len(sub_events)} events in this sub-chunk")
                all_events.extend(sub_events)
                time.sleep(1)
                
        except Exception as sub_e:
            print(f"    Error querying sub-chunk: {sub_e}")
            print(f"    Skipping this hour...")
            continue

print(f"\nTotal events found: {len(all_events)}")

# Save raw events to CSV
if all_events:
    # Convert the events to a list of dictionaries
    events_list = [dict(event) for event in all_events]
    
    # Convert to DataFrame
    df = pd.DataFrame(events_list)
    
    # Save to CSV
    df.to_csv('aerodrome_fee_changes_raw.csv', index=False)
    print(f"Saved {len(df)} raw events to aerodrome_fee_changes_raw.csv")
    
    # Show sample of the data
    print("\nSample of raw events:")
    print(df.head())
else:
    print("No events found in the specified time period")