from ..evm_models import EVMWebSocketHandler

class ArbitrumWebSocketHandler(EVMWebSocketHandler):
    def __init__(self, websocket_url):
        super().__init__(
            network_name="Arbitrum",
            websocket_url=websocket_url
        )
