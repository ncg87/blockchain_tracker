from ..base_models import BaseQuerier
from .evm_websocket_handler import EVMWebSocketHandler
from web3 import Web3
from typing import Optional
import requests
import json
from config import Settings
from abc import abstractmethod

class EVMQuerier(BaseQuerier):
    """
    Abstract EVM-specific querier with common functionality.
    """
    
    def __init__(self, network_name: str, http_endpoint: str, ws_endpoint: str):
        super().__init__(network_name)
        self.w3 = Web3(Web3.HTTPProvider(http_endpoint))
        self.ws = EVMWebSocketHandler(network_name, ws_endpoint)
    
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
    
    def get_block_logs(self, block_number):
        """
        Get the logs of a block.
        """
        self.logger.info(f"Fetching logs for block {block_number}")
        # Fetch logs for the block
        try:    
            logs = self.w3.eth.get_logs({
                "fromBlock": block_number,
                "toBlock": block_number
            })
            self.logger.debug(f"Logs fetched successfully for block {block_number}")
            return logs
        except Exception as e:
            self.logger.error(f"Failed to fetch logs for block {block_number}: {e}")
            return None
    
    async def stream_blocks(self, duration=None):
        """
        Stream blocks with full transactions using WebSocket.
        """
        async for full_block in self.ws.run(duration):
            if full_block:
                yield full_block
                
    @ abstractmethod
    def get_contract_abi(self, contract_address):
        """
        Get the ABI of a contract.
        """
        pass
    
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
    
    def get_contract(self, address, abi):
        try:
            if type(abi) == str:
                abi = json.loads(abi)
            return self.w3.eth.contract(address=address, abi=abi)
        except Exception as e:
            self.logger.error(f"Failed to get contract {address}: {e}")
            return None
