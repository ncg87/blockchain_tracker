from ..evm_models import EVMWebSocketHandler

class EthereumWebSocketHandler(EVMWebSocketHandler):
    def __init__(self, websocket_url):
        super().__init__("Ethereum", websocket_url)