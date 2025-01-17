import json
from typing import Optional, Dict, Any
from web3 import Web3
import psycopg2
from psycopg2.extras import DictCursor
from database import SQLInsertOperations, SQLQueryOperations
from dataclasses import dataclass

# For decoding the token contracts and getting the name, symbol, and decimals
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

@dataclass
class TokenInfo:
    address: str
    name: str
    symbol: str

@dataclass
class ContractInfo:
    address: str
    factory: str
    fee: int
    token0_name: str
    token1_name: str
    type: str

class EVMContractProcessor:
    def __init__(self, db, network: str, url):
        self.network = network
        self.sql_insert_ops = SQLInsertOperations(db)
        self.sql_query_ops = SQLQueryOperations(db)
        self.w3 = Web3(Web3.HTTPProvider(url))
        self.contract_info = {}

    def create_contract(self, address: str, abi: str) -> Optional[Any]:
        """Create a Web3 contract instance."""
        try:
            if isinstance(abi, str):
                abi = json.loads(abi)
            return self.w3.eth.contract(address=address, abi=abi)
        except Exception as e:
            print(f"Error creating contract for {address}: {e}")
            return None
    
    def process_contract(self, contract: Any) -> Optional[ContractInfo]:
        """Process a contract to extract relevant information."""
        try:
            
            
            
            # Check if contract has required methods
            required_methods = ['token0', 'token1', 'factory', 'fee']
            for method in required_methods:
                if not hasattr(contract.functions, method):
                    return None
            
            # Get token addresses
            token0_address = contract.functions.token0().call()
            token1_address = contract.functions.token1().call()

            # Create token contracts
            token0_contract = self.w3.eth.contract(
                address=token0_address, 
                abi=ERC20_ABI
            )
            token1_contract = self.w3.eth.contract(
                address=token1_address, 
                abi=ERC20_ABI
            )

            token0_info = self.sql_query_ops.query_evm_token_info(self.network, token0_address)
            # if token0_info is not found, create it
            if not token0_info:
                token0_info = TokenInfo(
                    address=token0_address,
                    name=token0_contract.functions.name().call(),
                    symbol=token0_contract.functions.symbol().call()
                )
                self.sql_insert_ops.insert_evm_token_info(self.network, token0_info)
            # if token1_info is not found, create it
            token1_info = self.sql_query_ops.query_evm_token_info(self.network, token1_address)
            if not token1_info:
                token1_info = TokenInfo(
                    address=token1_address,
                    name=token1_contract.functions.name().call(),
                    symbol=token1_contract.functions.symbol().call()
                )
                self.sql_insert_ops.insert_evm_token_info(self.network, token1_info)
            
            # create contract info
            contract_info = ContractInfo(
                address=contract.address,
                factory=contract.functions.factory().call(),
                fee=contract.functions.fee().call(),
                token0_name=token0_info.name,
                token1_name=token1_info.name,
                name=None,
            )
            self.sql_insert_ops.insert_evm_swap(contract_info)
            return contract_info

        except Exception as e:
            print(f"Error processing contract {contract.address}: {e}")
            return None