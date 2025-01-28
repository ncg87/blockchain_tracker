import json
import asyncio
from ..base_models import BaseWebSocketHandler

class XRPWebSocketHandler(BaseWebSocketHandler):
    def __init__(self, websocket_url):
        super().__init__("xrp", websocket_url)
        self.logger.info("Initializing XRPWebSocketHandler for XRP Ledger")

    def get_subscription_message(self):
        """
        Define the subscription message for XRP.
        """
        return {
            "command": "subscribe",
            "streams": ["ledger"]
        }

    def parse_message(self, message):
        """
        Parse incoming WebSocket messages for XRP.
        Extract ledger closure notifications.
        """
        if "type" in message and message["type"] == "ledgerClosed":
            return message["ledger_index"]
        return None

    async def fetch_full_data(self, ledger_index):
        """
        Fetch full ledger data, including transactions, using WebSocket requests.
        """
        tx_request = {
            "command": "ledger",
            "ledger_index": ledger_index,
            "transactions": True,
            "expand": True  # Include full transaction details
        }
        await self.connection.send(json.dumps(tx_request))
        response = await self.connection.recv()
        return json.loads(response).get("result")