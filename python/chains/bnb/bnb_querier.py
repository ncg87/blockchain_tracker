import requests
from config import Settings
from web3.middleware import ExtraDataToPOAMiddleware
from ..evm_models import EVMQuerier
import json
from web3 import Web3

class BNBQuerier(EVMQuerier):
    """
    BNB-specific querier.
    """
    
    def __init__(self):
        super().__init__('bnb', Settings.BNB_ENDPOINT, Settings.BNB_WEBSOCKET_ENDPOINT)
        
        # PoA middleware for BNB
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        
    def get_contract_abi(self, contract_address):
        """
        Override to use BSCScan API instead of Etherscan
        """
        # Similar to EVMQuerier.get_contract_abi but use Basescan
        self.logger.debug(f"Fetching ABI for contract {contract_address}")
        try:
            checksum_address = Web3.to_checksum_address(contract_address)
            url = "https://api.bscscan.com/api"
            params = {
                'module': 'contract',
                'action': 'getabi',
                'address': checksum_address,
                'apikey': Settings.BSCSCAN_API_KEY
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