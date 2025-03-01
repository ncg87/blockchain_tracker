from ..evm_models.evm_querier import EVMQuerier
from config import Settings
import requests
import json
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

class PolygonChainQuerier(EVMQuerier):
    """
    Polygon-specific querier implementation.
    """
    def __init__(self):
        super().__init__(
            network_name="polygon",
            http_endpoint=Settings.POLYGON_ENDPOINT,
            ws_endpoint=Settings.POLYGON_WEBSOCKET_ENDPOINT
        )
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    async def get_contract_abi(self, contract_address):
        """
        Override to use Polygonscan API
        """
        self.logger.debug(f"Fetching ABI for contract {contract_address}")
        try:
            checksum_address = Web3.to_checksum_address(contract_address)
            url = "https://api.polygonscan.com/api"
            params = {
                'module': 'contract',
                'action': 'getabi',
                'address': contract_address,
                'apikey': Settings.POLYGONSCAN_API_KEY
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
