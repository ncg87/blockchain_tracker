from solana.rpc.api import Client
from ..base_models import BaseQuerier
from config import Settings
import asyncio
from .solana_websocket_handler import SolanaWebSocketHandler

class SolanaQuerier(BaseQuerier):
    """
    Solana-specific querier.
    """
    
    def __init__(self):
        super().__init__('Solana')
        self.client = Client(Settings.SOLANA_ENDPOINT)
        self.ws = SolanaWebSocketHandler(Settings.SOLANA_WEBSOCKET_ENDPOINT)

    def is_connected(self) -> bool:
        """
        Check connection to the Solana RPC node.
        """
        try:
            slot_response = self.client.get_slot()
            return slot_response.get('result') is not None
        except Exception as e:
            self.logger.error(f"Failed to connect to Solana RPC: {e}")
            return False

    async def get_block(self, slot = None):
        """
        Fetch a block by slot. If slot is None, fetch the latest block.
        """
        try:
            # If a slot is not provided, fetch the latest block number
            if slot is None:
                self.logger.info("Fetching latest block slot.")
                slot = self.client.get_slot()
                slot = slot.value
            # Fetch the block data
            self.logger.info(f"Fetching block for slot: {slot}")
            block_object = self.client.get_block(
                slot,
                encoding="jsonParsed",
                max_supported_transaction_version=0
            )

            if not block_object:
                self.logger.warning(f"No block data found for slot: {slot}")
                return None

            self.logger.debug(f"Block {slot} fetched successfully.")
            return block_object.value
        except Exception as e:
            self.logger.error(f"Failed to fetch block for slot {slot}: {e}")
            raise
        
    async def stream_blocks(self, duration=None):
        """
        Stream blocks with full transactions using WebSocket.
        """
        async for full_block in self.ws.run(duration):
            yield full_block