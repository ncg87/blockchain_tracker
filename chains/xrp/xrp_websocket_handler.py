from ..base_models import BaseWebSocketHandler
import json


class XRPWebSocketHandler(BaseWebSocketHandler):
    def __init__(self, websocket_url):
        super().__init__("XRP Ledger", websocket_url)
        self.logger.info("Initializing XRPWebSocketHandler for XRP Ledger")

    def get_subscription_message(self):
        """
        Define the subscription message for XRP Ledger.
        Subscribe to both ledger updates and transactions.
        """
        return {
            "id": 1,
            "command": "subscribe",
            "streams": ["ledger", "transactions"]
        }

    def parse_message(self, message):
        """
        Parse incoming WebSocket messages for XRP Ledger.
        Extract relevant data based on the message type (ledger or transaction).
        """
        if "type" in message:
            if message["type"] == "ledgerClosed":
                return {"ledger_index": message["ledger_index"]}
            elif message["type"] == "transaction":
                return {
                    "tx_id": message["transaction"]["hash"],
                    "ledger_index": message["ledger_index"]
                }
        return None

    async def fetch_full_data(self, parsed_message):
        """
        Fetch full ledger or transaction details based on the parsed message.
        Use a separate REST or WebSocket request as needed.
        """
        if "ledger_index" in parsed_message and "tx_id" not in parsed_message:
            # Fetch full ledger details
            request_message = {
                "id": 2,
                "command": "ledger",
                "ledger_index": parsed_message["ledger_index"],
                "transactions": True,
                "expand": True
            }
        elif "tx_id" in parsed_message:
            # Fetch full transaction details
            request_message = {
                "id": 3,
                "command": "tx",
                "transaction": parsed_message["tx_id"]
            }
        else:
            return None
        await self.connection.send(json.dumps(request_message))
        response = await self.connection.recv()
        return json.loads(response).get("result")

