from config import Settings
from ..evm_models import EVMQuerier
import requests
import json
from web3 import Web3

class ArbitrumQuerier(EVMQuerier):
    """
    Arbitrum-specific querier.
    """
    def __init__(self):
        super().__init__('Arbitrum', Settings.ARBITRUM_ENDPOINT, Settings.ARBITRUM_WEBSOCKET_ENDPOINT)

    def get_contract_abi(self, contract_address):
        """
        Get the ABI of a contract.
        """
        self.logger.debug(f"Fetching ABI for contract {contract_address}")
        try:
            checksum_address = Web3.to_checksum_address(contract_address)
            url = "https://api.arbiscan.io/api"
            params = {
                'module': 'contract',
                'action': 'getabi',
                'address': checksum_address,
                'apikey': Settings.ARBISCAN_API_KEY
            }
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "1":
                    abi = json.loads(data["result"])
                    return abi
                else:
                    return None
            else:
                return None
        except Exception as e:
            return None 