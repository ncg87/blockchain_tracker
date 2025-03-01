#!/usr/bin/env python3
"""
Base Sepolia Logs Fetcher with Local Decoding
This script fetches raw logs from BaseScan API and decodes them using ABIs fetched separately
"""

import json
import requests
from web3 import Web3
from datetime import datetime
import os
import time  # Add this import

# Configuration - EDIT THESE VALUES
BASESCAN_API_KEY = "IAXNDZ79PZ51RDF37MH5RFYWW92F453VQ6"  # Replace with your BaseScan API key
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # Get script directory
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "decoded_logs")  # Set output dir relative to script
BASE_SEPOLIA_RPC = "https://base-sepolia.g.alchemy.com/v2/kKyUytmgJT2eE-A3mQUmU8xgbwFKm3FH"
ABI_CACHE_FILE = os.path.join(SCRIPT_DIR, "abi_cache.json")  # Set cache file relative to script
RATE_LIMIT_DELAY = 0.2  # 0.2 seconds between API calls (5 per second)

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(BASE_SEPOLIA_RPC))

# Load ABI cache from file if it exists
try:
    with open(ABI_CACHE_FILE, 'r') as f:
        try:
            abi_cache = json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in {ABI_CACHE_FILE}, creating new cache")
            abi_cache = {}
except FileNotFoundError:
    print(f"Creating new ABI cache file: {ABI_CACHE_FILE}")
    abi_cache = {}
    with open(ABI_CACHE_FILE, 'w') as f:
        json.dump(abi_cache, f)

def save_abi_cache():
    """Save the ABI cache to file"""
    with open(ABI_CACHE_FILE, 'w') as f:
        json.dump(abi_cache, f, indent=2)

def get_contract_abi(contract_address):
    """
    Get the contract ABI from BaseScan or cache
    Implements rate limiting and persistent caching
    """
    if contract_address in abi_cache:
        return abi_cache[contract_address]
    
    # Rate limiting
    time.sleep(RATE_LIMIT_DELAY)
    
    url = "https://api-sepolia.basescan.org/api"
    params = {
        'module': 'contract',
        'action': 'getabi',
        'address': contract_address,
        'apikey': BASESCAN_API_KEY
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if data['status'] == '1':
        try:
            abi = json.loads(data['result'])
            abi_cache[contract_address] = abi
            save_abi_cache()  # Save to file after successful fetch
            return abi
        except json.JSONDecodeError:
            print(f"Error: Invalid ABI format for {contract_address}")
            return None
    else:
        print(f"Error fetching ABI: {data.get('message', 'Unknown error')}")
        return None


def manually_add_abi(contract_address, abi_json):
    """
    Manually add an ABI to the cache and save to file
    """
    try:
        if isinstance(abi_json, str):
            abi = json.loads(abi_json)
        else:
            abi = abi_json
        
        abi_cache[contract_address] = abi
        save_abi_cache()  # Save to file after manual addition
        print(f"Added ABI for {contract_address} to cache")
        return True
    except Exception as e:
        print(f"Error adding ABI: {e}")
        return False


def get_event_signature(event_abi):
    """Calculate the event signature hash from the event ABI"""
    event_name = event_abi['name']
    input_types = [input_obj['type'] for input_obj in event_abi['inputs']]
    event_signature = f"{event_name}({','.join(input_types)})"
    event_hash = w3.keccak(text=event_signature).hex()
    return event_hash


def process_event_signatures(abi):
    """Process all events in the ABI to get their signatures"""
    events = {}
    for item in abi:
        if item['type'] == 'event':
            signature = get_event_signature(item)
            events[signature] = item
    return events


def fetch_logs(contract_address, from_block=0, to_block='latest'):
    """Fetch logs using BaseScan API with rate limiting"""
    time.sleep(RATE_LIMIT_DELAY)  # Add rate limiting
    
    url = "https://api-sepolia.basescan.org/api"
    params = {
        'module': 'logs',
        'action': 'getLogs',
        'address': contract_address,
        'fromBlock': from_block,
        'toBlock': to_block,
        'apikey': BASESCAN_API_KEY
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if data['status'] == '1':
        return data['result']
    else:
        error_msg = data.get('message', 'Unknown error')
        raise Exception(f"BaseScan API error: {error_msg}")


def decode_log(log, events_dict):
    """Decode a single log using the events dictionary"""
    result = {
        'address': log['address'],
        'blockNumber': int(log['blockNumber'], 16),
        'timeStamp': datetime.fromtimestamp(int(log['timeStamp'], 16)).strftime('%Y-%m-%d %H:%M:%S'),
        'transactionHash': log['transactionHash'],
        'topics': log['topics'],
        'data': log['data']
    }
    
    # Check if we have a matching event for the first topic (event signature)
    topic0 = log['topics'][0]
    if topic0 in events_dict:
        event = events_dict[topic0]
        result['event'] = event['name']
        
        # Decode parameters
        try:
            # Separate indexed and non-indexed inputs
            indexed_inputs = [i for i in event['inputs'] if i.get('indexed', False)]
            non_indexed_inputs = [i for i in event['inputs'] if not i.get('indexed', False)]
            
            # Process indexed parameters (from topics)
            indexed_params = {}
            for i, input_data in enumerate(indexed_inputs):
                # Topics[0] is the event signature, so we start from topics[1]
                if i + 1 < len(log['topics']):
                    topic_data = log['topics'][i+1]
                    
                    if input_data['type'] == 'address':
                        # For addresses, take the last 40 characters from the hex string
                        value = '0x' + topic_data[26:]
                        indexed_params[input_data['name']] = w3.to_checksum_address(value)
                    elif input_data['type'].startswith('uint'):
                        # For uints, convert from hex to decimal
                        indexed_params[input_data['name']] = int(topic_data, 16)
                    elif input_data['type'].startswith('bytes'):
                        # For bytes, keep as is
                        indexed_params[input_data['name']] = topic_data
                    else:
                        # For other types, convert as appropriate
                        indexed_params[input_data['name']] = topic_data
            
            # Process non-indexed parameters (from data)
            non_indexed_params = {}
            if non_indexed_inputs and log['data'] != '0x':
                # Create the types array for decoding
                types = [i['type'] for i in non_indexed_inputs]
                names = [i['name'] for i in non_indexed_inputs]
                
                # Decode the data field
                decoded_data = w3.codec.decode_abi(types, bytes.fromhex(log['data'][2:]))
                
                # Map the decoded values to parameter names
                for i, name in enumerate(names):
                    value = decoded_data[i]
                    # Convert to appropriate Python type
                    if isinstance(value, bytes):
                        try:
                            value = value.decode('utf-8').rstrip('\x00')
                        except UnicodeDecodeError:
                            value = '0x' + value.hex()
                    non_indexed_params[name] = value
            
            # Combine all parameters
            result['parameters'] = {**indexed_params, **non_indexed_params}
            result['decoded'] = True
            
        except Exception as e:
            result['decoded'] = False
            result['error'] = str(e)
    else:
        result['decoded'] = False
        result['error'] = "No matching event signature found in ABI"
    
    return result


def save_logs_to_file(contract_address, decoded_logs):
    """Save decoded logs to a file"""
    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # Create filename based on contract address
    filename = os.path.join(OUTPUT_DIR, f"{contract_address}.txt")
    
    with open(filename, 'w') as f:
        # Add header
        f.write(f"Decoded logs for contract {contract_address}\n")
        f.write(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Write each log
        for i, log in enumerate(decoded_logs, 1):
            f.write(f"Log #{i}\n")
            f.write(f"Block: {log.get('blockNumber')}\n")
            f.write(f"Time: {log.get('timeStamp')}\n")
            f.write(f"Transaction: {log.get('transactionHash')}\n")
            
            if log.get('decoded', False):
                f.write(f"Event: {log.get('event')}\n")
                f.write("Parameters:\n")
                for name, value in log.get('parameters', {}).items():
                    f.write(f"  {name}: {value}\n")
            else:
                f.write(f"Error: {log.get('error', 'Unknown error')}\n")
                f.write(f"Topics: {log.get('topics')}\n")
                f.write(f"Data: {log.get('data')}\n")
            
            f.write("\n" + "-"*80 + "\n\n")
    
    print(f"Saved decoded logs to {filename}")
    return filename


def process_contract(contract_address, from_block=0, to_block='latest', custom_abi=None):
    """
    Process logs for a specific contract
    If custom_abi is provided, use it instead of fetching from BaseScan
    """
    print(f"Processing contract: {contract_address}")
    
    # Get ABI
    if custom_abi:
        manually_add_abi(contract_address, custom_abi)
    
    abi = abi_cache.get(contract_address)
    if not abi:
        abi = get_contract_abi(contract_address)
    
    if not abi:
        print(f"No ABI available for {contract_address}. Cannot decode logs.")
        return False
    
    # Process events from ABI
    events_dict = process_event_signatures(abi)
    print(f"Found {len(events_dict)} events in the ABI")
    
    # Fetch logs
    try:
        logs = fetch_logs(contract_address, from_block, to_block)
        print(f"Fetched {len(logs)} logs")
        
        if not logs:
            print("No logs found for this contract")
            return True
        
        # Decode logs
        decoded_logs = [decode_log(log, events_dict) for log in logs]
        
        # Count successfully decoded logs
        success_count = sum(1 for log in decoded_logs if log.get('decoded', False))
        print(f"Successfully decoded {success_count} out of {len(decoded_logs)} logs")
        
        # Save to file
        save_logs_to_file(contract_address, decoded_logs)
        
        return True
    
    except Exception as e:
        print(f"Error processing contract {contract_address}: {e}")
        return False


def fetch_all_logs(from_block=0, to_block='latest'):
    """Fetch all logs from all contracts within the block range"""
    time.sleep(RATE_LIMIT_DELAY)
    
    url = "https://api-sepolia.basescan.org/api"
    params = {
        'module': 'logs',
        'action': 'getLogs',
        'fromBlock': from_block,
        'toBlock': to_block,
        'apikey': BASESCAN_API_KEY
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if data['status'] == '1':
        return data['result']
    else:
        error_msg = data.get('message', 'Unknown error')
        raise Exception(f"BaseScan API error: {error_msg}")

def process_all_logs(from_block=0, to_block='latest'):
    """Process all logs from all contracts"""
    print(f"Processing all logs from block {from_block} to {to_block}")
    
    try:
        logs = fetch_all_logs(from_block, to_block)
        print(f"Fetched {len(logs)} logs")
        
        # Group logs by contract address
        logs_by_contract = {}
        for log in logs:
            contract_address = log['address']
            if contract_address not in logs_by_contract:
                logs_by_contract[contract_address] = []
            logs_by_contract[contract_address].append(log)
        
        # Process each contract's logs
        for contract_address, contract_logs in logs_by_contract.items():
            print(f"\nProcessing contract: {contract_address}")
            
            # Get ABI if we don't have it
            if contract_address not in abi_cache:
                abi = get_contract_abi(contract_address)
                if not abi:
                    print(f"No ABI available for {contract_address}. Skipping log decoding.")
                    continue
            
            # Process events from ABI
            events_dict = process_event_signatures(abi_cache[contract_address])
            print(f"Found {len(events_dict)} events in the ABI")
            
            # Decode logs
            decoded_logs = [decode_log(log, events_dict) for log in contract_logs]
            
            # Count successfully decoded logs
            success_count = sum(1 for log in decoded_logs if log.get('decoded', False))
            print(f"Successfully decoded {success_count} out of {len(decoded_logs)} logs")
            
            # Save to file
            save_logs_to_file(contract_address, decoded_logs)
        
        return True
    
    except Exception as e:
        print(f"Error processing logs: {e}")
        return False

def main():
    print("Base Sepolia All Logs Fetcher with Local Decoding")
    print("=" * 50)
    
    last_processed_block = w3.eth.block_number  # Start from current block
    print(f"Starting from block {last_processed_block}")
    
    while True:
        try:
            current_block = w3.eth.block_number
            
            # Only process new blocks
            if last_processed_block < current_block:
                print(f"\nProcessing blocks {last_processed_block} to {current_block}")
                
                success = process_all_logs(
                    from_block=last_processed_block,
                    to_block=current_block
                )
                
                if success:
                    last_processed_block = current_block
            
            # Wait before next iteration
            print("\nWaiting for new blocks...")
            time.sleep(15)  # Wait 15 seconds before checking for new blocks
            
        except KeyboardInterrupt:
            print("\nStopping log monitoring...")
            break
        except Exception as e:
            print(f"\nError in main loop: {e}")
            time.sleep(30)  # Wait longer if there's an error
            continue

if __name__ == "__main__":
    main()