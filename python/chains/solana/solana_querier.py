from solana.rpc.api import Client
from ..base_models import BaseQuerier
from config import Settings
import asyncio
import json
from .solana_websocket_handler import SolanaWebSocketHandler
from solana.rpc.api import RPCException

class SolanaQuerier(BaseQuerier):
    """
    Solana-specific querier.
    """
    
    def __init__(self):
        super().__init__('solana')
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
            # Convert block to a dictionary
            return json.loads(block_object.to_json())['result']
        except RPCException as e:
            if "Block not available" in str(e):
                self.logger.warning(f"Block {slot} not available, skipping...")
                return None
            raise 
        except Exception as e:
            self.logger.error(f"Failed to fetch block for slot {slot}: {e}")
            raise
        
    async def stream_blocks(self, duration=None):
        """
        Stream blocks using WebSocket and fetch block details concurrently.
        """
        self.logger.info("Starting block streaming...")
        start_time = asyncio.get_running_loop().time()
        
        # Keep track of the last processed slot to avoid duplicates
        last_processed_slot = None

        async for ws_slot in self.ws.run(duration):
            if duration and asyncio.get_running_loop().time() - start_time > duration:
                self.logger.info("Stream duration expired.")
                break
                
            if ws_slot is not None:
                try:
                    # Get current slot from RPC
                    current_slot = self.client.get_slot().value
                    slot_diff = ws_slot - current_slot
                    
                    # Only process if we haven't seen this slot before
                    if last_processed_slot and ws_slot <= last_processed_slot:
                        continue
                    
                    # If WebSocket slot is ahead of RPC slot, wait for RPC to catch up
                    if slot_diff > 0:
                        self.logger.debug(f"Waiting for slot {ws_slot} to be available (current: {current_slot})")
                        await asyncio.sleep(1)  # Wait a bit for RPC to catch up
                        continue
                    
                    # Try to fetch the block
                    block = await self.get_block(ws_slot)
                    if block:
                        last_processed_slot = ws_slot
                        self.logger.info(f"Successfully fetched and processing block {ws_slot}")
                        yield block
                    else:
                        self.logger.debug(f"No block data available for slot {ws_slot}")
                        
                except Exception as e:
                    self.logger.error(f"Error processing slot {ws_slot}: {e}")
                    continue