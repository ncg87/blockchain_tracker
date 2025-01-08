from ..base_models import BaseQuerier
from .xrp_websocket_handler import XRPWebSocketHandler
from xrpl.clients import JsonRpcClient
from config import Settings
from typing import Optional
from xrpl.models import ServerInfo, Ledger
import nest_asyncio


class XRPQuerier(BaseQuerier):
    """
    XRP-specific querier for fetching ledger data.
    """
    def __init__(self):
        super().__init__('XRP')
        nest_asyncio.apply()
        self.client = JsonRpcClient(Settings.XRP_ENDPOINT)
        self.ws = XRPWebSocketHandler(Settings.XRP_WEBSOCKET_ENDPOINT)

    def is_connected(self) -> bool:
        """
        Check if the connection to the provider is successful.
        """
        try:
            response = self.client.request(ServerInfo())
            return 'info' in response.result
        except Exception as e:
            self.logger.error(f"Connection check failed: {e}")
            return False

    def get_block(self, block_number: Optional[int] = None):
        """
        Fetch a block (ledger) by number. If not specified, fetch the latest ledger.
        """
        try:
            if block_number is None:
                # Get the latest validated ledger index
                response = self.client.request(ServerInfo())
                block_number = response.result['info']['validated_ledger']['seq']

            self.logger.info(f"Fetching ledger {block_number}")

            # Fetch the ledger data with transactions
            ledger_request = Ledger(
                ledger_index=block_number,
                transactions=True,
                expand=True
            )
            response = self.client.request(ledger_request)
            return response.result
        except Exception as e:
            self.logger.error(f"Failed to fetch ledger {block_number}: {e}")
            return None
        
    async def stream_blocks(self, duration=None):
        """
        Stream blocks with full transactions using WebSocket.
        """
        async for full_block in self.ws.run(duration):
            yield full_block
