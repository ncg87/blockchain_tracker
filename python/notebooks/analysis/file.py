import sys
import os
from pathlib import Path

# Get absolute path to project root
project_root = Path(os.getcwd()).resolve()
if project_root.name != "ncg87-blockchain_tracker":
    project_root = project_root.parent  # Adjust if running from a subdirectory

sys.path.append(str(project_root))

# Add to Python path if not already there
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import Settings

from database import MongoDatabase, MongoInsertOperations, MongoQueryOperations
from database import SQLDatabase, SQLInsertOperations, SQLQueryOperations

import json
import web3


sql_db = SQLDatabase()
w3 = web3.Web3(web3.HTTPProvider(Settings.BASE_ENDPOINT))


query = "SELECT * FROM evm_contract_abis WHERE network = 'Base'"
sql_db.cursor.execute(query)
contract_abis = sql_db.cursor.fetchall()

len(contract_abis)

contract_list = []

for abi in contract_abis:
    if abi[2] is None:
        continue
    abi_json = json.loads(abi[2])
    contract = w3.eth.contract(abi[1], abi = abi_json)
    contract_list.append(contract)

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]

from concurrent.futures import ThreadPoolExecutor, as_completed

def process_contract(args):
    i, contract = args
    try:
        token_0 = contract.functions.token0().call()
        token_1 = contract.functions.token1().call()
        token0_contract = w3.eth.contract(address=token_0, abi=ERC20_ABI)
        token1_contract = w3.eth.contract(address=token_1, abi=ERC20_ABI)
        contract_factory = contract.functions.factory().call()
        contract_fee = contract.functions.fee().call()
        contract_token0 = token0_contract.functions.name().call()
        contract_token1 = token1_contract.functions.name().call()
        
        return (i, {
            'address': contract.address,
            'factory': contract_factory,
            'fee': contract_fee,
            'token0_name': contract_token0,
            'token1_name': contract_token1
        })
    except Exception as e:
        print(f"Error processing contract {i}: {e}")
        return (i, None)

# Use ThreadPoolExecutor since we're doing I/O-bound operations
contract_info = []
max_workers = 10  # Adjust this number based on your needs

with ThreadPoolExecutor(max_workers=max_workers) as executor:
    # Create futures for all contracts
    futures = [executor.submit(process_contract, (i, contract)) 
              for i, contract in enumerate(contract_list)]
    
    # Process completed futures as they finish
    for future in as_completed(futures):
        i, result = future.result()
        if result:
            contract_info.append(result)
            print(f"Processed contract {i}: {result['token0_name']} - {result['token1_name']}")
            
factory_group = {}
for contract in contract_info:
    if contract['factory'] not in factory_group:
        factory_group[contract['factory']] = []
    factory_group[contract['factory']].append(contract)
