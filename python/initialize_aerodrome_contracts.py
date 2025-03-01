from web3 import Web3
from config import Settings
from database import MongoDatabase, SQLDatabase, DatabaseOperator
import json
import csv
from chains import BaseChainQuerier
import asyncio


querier = BaseChainQuerier()
w3 = Web3(Web3.HTTPProvider(Settings.BASE_ENDPOINT))
db_operator = DatabaseOperator(SQLDatabase(), MongoDatabase())

# Gets the aerodrome factory contract, to determine fees
def get_aerodrome_factory_contract():
    abi = db_operator.sql.query.evm.query_contract_abi('base','0xbe720274c24b5Ec773559b8C7e28c2503DaC7645')
    contract = w3.eth.contract(address='0xbe720274c24b5Ec773559b8C7e28c2503DaC7645', abi=json.loads(abi['abi']))
    return contract

# Gets the pool contract, to determine if it is stable or not
def get_pool_contract(pool_address):
    abi = db_operator.sql.query.evm.query_contract_abi('base',pool_address)
    contract = w3.eth.contract(address=pool_address, abi=json.loads(abi['abi']))
    return contract

# Gets the list of all pool addresses for Aerodrome
QUERY_SWAP_INFOS = """
    SELECT contract_address
    FROM evm_swap_info
    WHERE factory_address = '0xbe720274c24b5Ec773559b8C7e28c2503DaC7645';
"""
db_operator.sql.db.cursor.execute(QUERY_SWAP_INFOS,)

results = db_operator.sql.db.cursor.fetchall()

async def process_pools():
    factory_contract = get_aerodrome_factory_contract()
    
    with open('citadel_pools2.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['pool_address', 'is_stable', 'fee'])
        
        for result in results:
            pool_address = result['contract_address']
            abi = await querier.get_contract_abi(pool_address)
            db_operator.sql.insert.evm.contract_abi('base',pool_address,abi)
            pool_contract = get_pool_contract(pool_address)
            is_stable = pool_contract.functions.stable().call()
            fee = factory_contract.functions.getFee(pool_address, is_stable).call()
            writer.writerow([pool_address, is_stable, fee])
            print(f"Processed pool: {pool_address} - {is_stable} - {fee}")

# Run the async function
asyncio.run(process_pools())


