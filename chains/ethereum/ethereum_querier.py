import requests
import web3
from ..base_models import BaseQuerier
from typing import Optional
from config import Settings
import logging
from web3 import Web3

from .ethereum_websocket_handler import EthereumWebSocketHandler
class EthereumQuerier(BaseQuerier):
    """
    Ethereum-specific querier.
    """
    
    def __init__(self):
        super().__init__('Ethereum')
        self.w3 = Web3(Web3.HTTPProvider(Settings.ETHEREUM_ENDPOINT))
        self.ws = EthereumWebSocketHandler(Settings.ETHEREUM_WEBSOCKET_ENDPOINT)
    
    def is_connected(self) -> bool:
        """
        Check if the connection to the provider is successful.
        """
        return self.w3.is_connected()

    async def get_block(self, block_number: Optional[int] = None):
        """
        Fetch a block by number. If not specified, fetch the latest block.
        """
        self.logger.info(f"Fetching block {'latest' if block_number is None else block_number}")
        try:
            block = self.w3.eth.get_block('latest' if block_number is None else block_number, full_transactions=True)
            self.logger.debug(f"Block {block['number']} fetched successfully.")
            return block
        except Exception as e:
            self.logger.error(f"Failed to fetch block: {e}")
            raise
            
    async def stream_blocks(self, duration=None):
        """
        Stream blocks with full transactions using WebSocket.
        """
        async for full_block in self.ws.run(duration):
            if full_block:
                yield full_block


    
    def get_contract_abi(self, contract_address):
        """
        Get the ABI of a contract.
        """
        self.logger.info(f"Fetching ABI for contract {contract_address}")
        try:
            url = "https://api.etherscan.io/api"
            params = {
                'module': 'contract',
                'action': 'getabi',
                'address': contract_address,
                'apikey': Settings.ETHERSCAN_API_KEY
            }
            response = requests.get(url, params=params)
            abi = response.json().get('result', None)
            if abi == 'Contract source code not verified':
                self.logger.warning(f"Contract {contract_address} source code not verified.")
                return None
            self.logger.debug(f"ABI for {contract_address} fetched successfully.")
            return abi
        except Exception as e:
            self.logger.error(f"Failed to fetch ABI: {e}")
            return None
    
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
    
    def decode_input_data(self, input_data, address, abi):
        """
        Decode the input data of a transaction.
        """
        try:
            contract = self.w3.eth.contract(address=address, abi=abi)
            decoded = contract.decode_function_input(input_data)
            self.logger.debug(f"Input data decoded successfully for {address}")
            return decoded
        except Exception as e:
            self.logger.error(f"Failed to decode input data for {address}: {e}")
            return None
