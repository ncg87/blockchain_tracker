from ..evm_models.evm_websocket_handler import EVMWebSocketHandler

class BaseChainWebSocketHandler(EVMWebSocketHandler):
    """
    Base-specific WebSocket handler implementation.
    """
    def __init__(self, websocket_url: str):
        super().__init__(
            network_name="Base",
            websocket_url=websocket_url
        )
