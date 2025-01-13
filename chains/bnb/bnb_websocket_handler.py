from ..evm_models import EVMWebSocketHandler

class BNBWebSocketHandler(EVMWebSocketHandler):
    def __init__(self, websocket_url):
        super().__init__("BNB", websocket_url)
