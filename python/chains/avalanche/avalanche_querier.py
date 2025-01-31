from ..evm_models.evm_querier import EVMQuerier
from config import Settings
import requests
import json
from web3 import Web3

class AvalancheChainQuerier(EVMQuerier):
    """
    Avalanche-specific querier implementation.
    """
    def __init__(self):
        super().__init__(
            network_name="avalanche",
            http_endpoint=Settings.AVALANCHE_ENDPOINT,
            ws_endpoint=Settings.AVALANCHE_WEBSOCKET_ENDPOINT
        )

    async def get_contract_abi(self, contract_address):
        """
        Override to use Snowtrace API instead of Etherscan
        """
        self.logger.debug(f"Fetching ABI for contract {contract_address}")
        try:
            checksum_address = Web3.to_checksum_address(contract_address)
            url = "https://api.snowtrace.io/api"
            params = {
                'module': 'contract',
                'action': 'getabi',
                'address': contract_address,
                'apikey': Settings.SNOWSCAN_API_KEY
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
