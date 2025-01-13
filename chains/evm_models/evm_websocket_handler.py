from ..base_models import BaseWebSocketHandler
import json

class EVMWebSocketHandler(BaseWebSocketHandler):
    """
    Abstract WebSocket handler for EVM-compatible chains.
    """
    def __init__(self, network_name: str, websocket_url: str):
        super().__init__(network_name, websocket_url)
        self.logger.info(f"Initializing EVMWebSocketHandler for {network_name}")
        

    def get_subscription_message(self):
        """
        Define the subscription message for EVM chains.
        """
        return {
            "jsonrpc": "2.0",
            "method": "eth_subscribe",
            "params": ["newHeads"],
            "id": 1
        }

    def parse_message(self, message):
        """
        Parse incoming WebSocket messages for EVM chains.
        Extract the block number from the message.
        """
        if "params" in message and "result" in message["params"]:
            return int(message["params"]["result"]["number"], 16)
        return None

    async def fetch_full_data(self, block_number):
        """
        Fetch full block data, including transactions, using JSON-RPC.
        """
        request_message = {
            "jsonrpc": "2.0",
            "method": "eth_getBlockByNumber",
            "params": [hex(block_number), True],  # Full transactions requested
            "id": 1
        }
        await self.connection.send(json.dumps(request_message))
        response = await self.connection.recv()
        return json.loads(response).get("result")