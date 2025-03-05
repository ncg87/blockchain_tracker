#!/usr/bin/env python
import csv
import os
import argparse
import asyncio
import json
import time
from web3 import Web3
from database import SQLDatabase, DatabaseOperator, MongoDatabase
from config import Settings
from chains import BaseChainProcessor, BaseChainQuerier

# Create a semaphore to limit concurrent API calls to Etherscan
API_RATE_LIMIT = 5  # 5 requests per second
api_semaphore = asyncio.Semaphore(API_RATE_LIMIT)
last_api_call_time = {}  # Track last API call time per second

querier = BaseChainQuerier()
processor = BaseChainProcessor(SQLDatabase(), MongoDatabase(), querier)

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(Settings.BASE_ENDPOINT))

async def rate_limited_api_call(token_address):
    """
    Execute an API call to Etherscan with rate limiting.
    
    Args:
        token_address (str): The token contract address
        
    Returns:
        The result of the API call
    """
    # Calculate the current second
    current_second = int(time.time())
    
    # Initialize counter for this second if it doesn't exist
    if current_second not in last_api_call_time:
        last_api_call_time.clear()  # Clear old entries
        last_api_call_time[current_second] = 0
    
    # Check if we've hit the rate limit for this second
    if last_api_call_time[current_second] >= API_RATE_LIMIT:
        # Wait until the next second
        wait_time = 1.0 - (time.time() - current_second)
        if wait_time > 0:
            print(f"Rate limit reached, waiting {wait_time:.2f} seconds...")
            await asyncio.sleep(wait_time)
        # Reset for the new second
        current_second = int(time.time())
        last_api_call_time.clear()
        last_api_call_time[current_second] = 0
    
    # Increment the counter for this second
    last_api_call_time[current_second] += 1
    
    # Execute the API call
    async with api_semaphore:
        return await querier.get_contract_abi(token_address)

async def check_agent_key(token_address, db_operator):
    """
    Check if a token is an agent key by attempting to call fee-related functions.
    
    Args:
        token_address (str): The token contract address
        db_operator: Database operator for querying ABIs
        
    Returns:
        tuple: (is_agent_key, total_sell_fee, pair_address)
    """
    try:
        # Get the token ABI from the database
        abi_result = db_operator.sql.query.evm.query_contract_abi('base', token_address)
        
        # Initialize abi variable
        abi = None
        
        if not abi_result:
            print(f"No ABI found for token {token_address}, fetching from Etherscan...")
            try:
                # Use rate-limited API call
                abi = await rate_limited_api_call(token_address)
                if abi:
                    print(f"Successfully fetched ABI for {token_address} from Etherscan")
                    # Store the ABI in the database for future use
                    db_operator.sql.insert.evm.contract_abi('base', token_address, json.dumps(abi))
                    # Process the token to get its metadata
                    await processor.log_processor._process_token(token_address)
                else:
                    print(f"Failed to fetch ABI for {token_address} from Etherscan")
                    return False, None, None
            except Exception as e:
                print(f"Error fetching ABI for {token_address} from Etherscan: {e}")
                return False, None, None
        else:
            # ABI exists in database
            if abi_result.get('abi'):
                try:
                    abi = json.loads(abi_result['abi'])
                    print(f"Using ABI from database for {token_address}")
                except json.JSONDecodeError:
                    print(f"Invalid ABI format in database for {token_address}")
                    return False, None, None
            else:
                print(f"Empty ABI in database for {token_address}")
                return False, None, None
        
        # If we still don't have a valid ABI, return
        if not abi:
            print(f"No valid ABI available for {token_address}")
            return False, None, None
            
        # Create contract instance
        token_contract = w3.eth.contract(address=token_address, abi=abi)
        
        # Check if the contract has the agent key-related functions
        has_admin_fee_function = any(
            func.get('name') == 'adminSellFeePercent' 
            for func in abi if isinstance(func, dict) and 'name' in func
        )
        
        has_creator_fee_function = any(
            func.get('name') == 'creatorSellFeePercent' 
            for func in abi if isinstance(func, dict) and 'name' in func
        )
        
        has_pair_function = any(
            func.get('name') == 'pair' 
            for func in abi if isinstance(func, dict) and 'name' in func
        )
        
        # Check if this is likely an agent key contract
        if not (has_admin_fee_function and has_creator_fee_function and has_pair_function):
            return False, None, None
        
        # Try to call the fee-related functions
        try:
            admin_sell_fee = token_contract.functions.adminSellFeePercent().call()
            creator_sell_fee = token_contract.functions.creatorSellFeePercent().call()
            pair_address = token_contract.functions.pair().call()
            
            # Calculate total sell fee
            total_sell_fee = admin_sell_fee + creator_sell_fee
            
            print(f"Found agent key: {token_address} with total sell fee: {total_sell_fee}, pair: {pair_address}")
            return True, total_sell_fee, pair_address
        except Exception as e:
            print(f"Error calling functions on {token_address}: {e}")
            # Not an agent key or doesn't have these functions
            return False, None, None
            
    except Exception as e:
        print(f"Error checking token {token_address}: {e}")
        return False, None, None

def get_processed_tokens(output_file):
    """
    Get a set of already processed token addresses from the output file.
    
    Args:
        output_file (str): Path to the output CSV file
        
    Returns:
        set: Set of processed token addresses
    """
    processed_tokens = set()
    
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                next(reader)  # Skip header
                for row in reader:
                    if row and len(row) > 0:
                        processed_tokens.add(row[0])  # Add contract address
        except Exception as e:
            print(f"Error reading existing output file: {e}")
    
    return processed_tokens

async def export_agent_keys(output_file="base_agent_keys.csv", batch_size=50):
    """
    Export all agent keys from the Base chain to a CSV file.
    
    Args:
        output_file (str): Path to the output CSV file
        batch_size (int): Number of tokens to process in each batch
    """
    # Initialize database connections
    mongodb = MongoDatabase()
    sql_db = SQLDatabase()
    db_operator = DatabaseOperator(sql_db, mongodb)
    
    try:
        # Check Web3 connection
        if not w3.is_connected():
            print("Error: Cannot connect to Base network. Please check your connection.")
            return
            
        # Get already processed tokens
        processed_tokens = get_processed_tokens(output_file)
        print(f"Found {len(processed_tokens)} already processed tokens")
        
        # Query to get all token addresses for the Base chain
        query = """
            SELECT contract_address
            FROM evm_token_info
            WHERE chain = 'base'
            ORDER BY contract_address
        """
        
        # Execute the query
        db_operator.sql.db.cursor.execute(query)
        all_tokens = db_operator.sql.db.cursor.fetchall()
        
        # Filter out already processed tokens
        tokens = [token for token in all_tokens if token['contract_address'] not in processed_tokens]
        
        print(f"Found {len(all_tokens)} total tokens on Base chain")
        print(f"Remaining tokens to process: {len(tokens)}")
        
        # Check if we need to create a new file or append to existing
        file_exists = os.path.exists(output_file) and os.path.getsize(output_file) > 0
        
        # Prepare CSV file
        with open(output_file, 'a' if file_exists else 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header if creating a new file
            if not file_exists:
                writer.writerow(['contract_address', 'is_agent_key', 'total_sell_fee', 'pair_address'])
            
            # Process tokens in batches to avoid overwhelming the system
            total_tokens = len(tokens)
            agent_keys_count = 0
            
            for i in range(0, total_tokens, batch_size):
                batch = tokens[i:i+batch_size]
                print(f"Processing batch {i//batch_size + 1}/{(total_tokens + batch_size - 1)//batch_size}...")
                
                # Process batch concurrently
                tasks = []
                for token in batch:
                    token_address = token['contract_address']
                    tasks.append(check_agent_key(token_address, db_operator))
                
                results = await asyncio.gather(*tasks)
                
                # Write results to CSV
                for j, token in enumerate(batch):
                    token_address = token['contract_address']
                    is_agent_key, total_sell_fee, pair_address = results[j]
                    
                    writer.writerow([
                        token_address,
                        is_agent_key,
                        total_sell_fee if is_agent_key else '',
                        pair_address if is_agent_key else ''
                    ])
                    
                    if is_agent_key:
                        agent_keys_count += 1
                
                # Save progress after each batch
                csvfile.flush()
                os.fsync(csvfile.fileno())
                print(f"Progress saved after processing batch {i//batch_size + 1}")
                
                print(f"Processed {min(i+batch_size, total_tokens)}/{total_tokens} tokens")
        
        print(f"Found {agent_keys_count} agent keys")
        print(f"Successfully exported agent key information to {output_file}")
    
    except Exception as e:
        print(f"Error exporting agent key information: {e}")
    
    finally:
        # Close the database connections
        sql_db.close()

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Export Base chain agent keys to CSV')
    parser.add_argument('--output', '-o', default='base_agent_keys.csv',
                        help='Output CSV file path (default: base_agent_keys.csv)')
    parser.add_argument('--batch-size', '-b', type=int, default=50,
                        help='Number of tokens to process in each batch (default: 50)')
    
    args = parser.parse_args()
    
    # Run the export function with the provided arguments
    asyncio.run(export_agent_keys(
        output_file=args.output,
        batch_size=args.batch_size
    )) 