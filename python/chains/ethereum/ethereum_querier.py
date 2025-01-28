from config import Settings
from ..evm_models import EVMQuerier
import requests
import json
from web3 import Web3

class EthereumQuerier(EVMQuerier):
    """
    Ethereum-specific querier.
    """
    def __init__(self):
        super().__init__('ethereum', Settings.ETHEREUM_ENDPOINT, Settings.ETHEREUM_WEBSOCKET_ENDPOINT)

    async def get_contract_abi(self, contract_address):
        """
        Get the ABI of a contract.
        """
        self.logger.debug(f"Fetching ABI for contract {contract_address}")
        try:
            checksum_address = Web3.to_checksum_address(contract_address)
            url = "https://api.etherscan.io/api"
            params = {
                'module': 'contract',
                'action': 'getabi',
                'address': checksum_address,
                'apikey': Settings.ETHERSCAN_API_KEY
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "1":
                    abi = json.loads(data["result"])
                    return abi
                else:
                    #self.logger.error(f"Failed to fetch ABI: {data['message']}")
                    return None
            else:
                #self.logger.error(f"Failed to fetch ABI: {response.status_code}")
                return None
        except Exception as e:
            #self.logger.error(f"Failed to fetch ABI: {e}")
            return None
