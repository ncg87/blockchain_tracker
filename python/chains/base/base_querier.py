from ..evm_models.evm_querier import EVMQuerier
from config import Settings
import requests
import json

class BaseChainQuerier(EVMQuerier):
    """
    Base-specific querier implementation.
    """
    def __init__(self):
        super().__init__(
            network_name="base",
            http_endpoint=Settings.BASE_ENDPOINT,
            ws_endpoint=Settings.BASE_WEBSOCKET_ENDPOINT
        )

    def get_contract_abi(self, contract_address):
        """
        Override to use Basescan API instead of Etherscan
        """
        # Similar to EVMQuerier.get_contract_abi but use Basescan
        self.logger.debug(f"Fetching ABI for contract {contract_address}")
        try:
            url = "https://api.basescan.org/api"
            params = {
                'module': 'contract',
                'action': 'getabi',
                'address': contract_address,
                'apikey': Settings.BASESCAN_API_KEY
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
    