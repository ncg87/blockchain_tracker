import requests
from config import Settings
from web3.middleware import ExtraDataToPOAMiddleware
from ..evm_models import EVMQuerier


class BNBQuerier(EVMQuerier):
    """
    BNB-specific querier.
    """
    
    def __init__(self):
        super().__init__('BNB', Settings.BNB_ENDPOINT, Settings.BNB_WEBSOCKET_ENDPOINT)
        
        # PoA middleware for BNB
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)