from ..evm_models.evm_querier import EVMQuerier
from config import Settings
import requests
import json
from web3 import Web3

class MantleQuerier(EVMQuerier):
    """
    Mantle-specific querier implementation.
    """
    def __init__(self):
        super().__init__(
            network_name="mantle",
            http_endpoint=Settings.MANTLE_ENDPOINT,
            ws_endpoint=Settings.MANTLE_WEBSOCKET_ENDPOINT
        )

    async def get_contract_abi(self, contract_address):
        """
        Override to use Mantle API
        """
        self.logger.debug(f"Fetching ABI for contract {contract_address}")
        try:
            checksum_address = Web3.to_checksum_address(contract_address)
            url = "https://explorer.mantle.xyz/api"
            params = {
                'module': 'contract',
                'action': 'getabi',
                'address': checksum_address,
                'apikey': Settings.MANTLESCAN_API_KEY
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