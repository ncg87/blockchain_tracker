from ..base_models import BaseQuerier
import requests
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from config import Settings
import asyncio

class BitcoinQuerier(BaseQuerier):
    """
    Bitcoin-specific querier for fetching block data.
    """

    def __init__(self):
        super().__init__('Bitcoin')
        self.endpoint_url = Settings.BITCOIN_ENDPOINT
        self.headers = {
            "Content-Type": "application/json"
        }
        # For streaming blocks
        self.poll_interval = 5
        self.latest_block_hash = None
        
        self.logger.info("BitcoinQuerier initialized")
        

    async def _make_rpc_call(self, method: str, params: list = []) -> Dict[str, Any]:
        """
        Helper method to make an RPC call to the Bitcoin node.
        """
        payload = {
            "jsonrpc": "1.0",
            "id": "query",
            "method": method,
            "params": params
        }
        response = requests.post(
            self.endpoint_url,
            json=payload,
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()['result']

    async def is_connected(self) -> bool:
        """
        Check if the connection to the Bitcoin node is successful.
        """
        self.logger.info("Checking Bitcoin node connection")
        try:
            await self._make_rpc_call("getblockchaininfo")
            return True
        except Exception as e:
            self.logger.error(f"Connection check failed: {e}")
            return False

    async def get_block(self, block_number: Optional[int] = None) -> Dict[str, Any]:
        """
        Fetch a block by height or fetch the latest block if height is not specified.
        """
        try:
            if block_number is None:
                self.logger.info("Fetching the most recent block")
                block_height = await self._make_rpc_call("getblockcount")
            else:
                self.logger.info(f"Fetching block {block_number}")
                block_height = block_number

            # Get block hash and full block data
            block_hash = await self._make_rpc_call("getblockhash", [block_height])
            block_data = await self._make_rpc_call("getblock", [block_hash, 2])  # Verbosity 2 includes transactions
            
            # Add metadata for processing
            block_data['retrieved_at'] = datetime.utcnow().isoformat()
            block_data['height'] = block_height
            
            return block_data
        except Exception as e:
            self.logger.error(f"Failed to fetch block {block_number}: {e}")
            return None
    
    async def stream_blocks(self, duration: Optional[int] = None):
        """
        Stream blocks by polling for new blocks.
        Runs for the specified duration (in seconds) or indefinitely if duration is None.
        """
        self.logger.info("Starting block stream...")
        end_time = None if duration is None else asyncio.get_running_loop().time() + duration

        while True:
            try:
                # Fetch the latest block hash
                latest_block_hash = await self._make_rpc_call("getbestblockhash")

                # Check if it's a new block
                if latest_block_hash != self.latest_block_hash:
                    self.latest_block_hash = latest_block_hash
                    self.logger.info(f"New block detected: {latest_block_hash}")

                    # Fetch full block data
                    full_block_data = await self.get_block()
                    if full_block_data:
                        yield full_block_data
                else:
                    self.logger.debug("No new block detected.")
            except Exception as e:
                self.logger.error(f"Error during block streaming: {e}")

            # Break if duration is reached
            if end_time and asyncio.get_running_loop().time() >= end_time:
                self.logger.info("Block streaming duration ended.")
                break

            # Wait before polling again
            await asyncio.sleep(self.poll_interval)
