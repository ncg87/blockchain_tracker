import requests
import web3
from base_models import BaseQuerier
from typing import Optional

class EthereumQuerier(BaseQuerier):
    """
    Ethereum-specific querier.
    """
    
    def __init__(self, provider: str):
        super().__init__(provider)

    def get_block(self, block_number: Optional[int] = None):
        """
        Fetch a block by number. If not specified, fetch the latest block.
        """
        if not self.is_connected():
            raise ConnectionError("Failed to connect to the Ethereum provider.")
        
        if block_number is None:
            return self.w3.eth.get_block('latest', full_transactions=True)
        
        return self.w3.eth.get_block(block_number, full_transactions=True)
 
    def get_contract_abi(self, contract_address):
        """
        Get the ABI of a contract.
        """
        url = "https://api.etherscan.io/api"
        params = {
            'module': 'contract',
            'action': 'getabi',
            'address': contract_address,
            'apikey': self.etherscan_api_key
        }
        response = requests.get(url, params=params)
        return response.json()['result']
    
    def is_contract(self, address):
        """
        Check if an address is a contract or an EOA (Externally Owned Account).
        """
        # Some transactions (e.g., contract creation) have no "to" address
        if address is None:
            return False
        code = self.w3.eth.get_code(address)
        # True for contracts, False for EOAs
        return len(code) > 0 