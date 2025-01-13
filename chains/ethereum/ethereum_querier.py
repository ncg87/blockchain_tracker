from config import Settings
from ..evm_models import EVMQuerier
class EthereumQuerier(EVMQuerier):
    """
    Ethereum-specific querier.
    """
    def __init__(self):
        super().__init__('Ethereum', Settings.ETHEREUM_ENDPOINT, Settings.ETHEREUM_WEBSOCKET_ENDPOINT)

    
