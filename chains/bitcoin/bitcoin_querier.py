from ..base_models import BaseQuerier
import requests
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from config import Settings


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
        self.logger.info("BitcoinQuerier initialized")

    def _make_rpc_call(self, method: str, params: list = []) -> Dict[str, Any]:
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

    def is_connected(self) -> bool:
        """
        Check if the connection to the Bitcoin node is successful.
        """
        self.logger.info("Checking Bitcoin node connection")
        try:
            self._make_rpc_call("getblockchaininfo")
            return True
        except Exception as e:
            self.logger.error(f"Connection check failed: {e}")
            return False

    def get_block(self, block_number: Optional[int] = None) -> Dict[str, Any]:
        """
        Fetch a block by height or fetch the latest block if height is not specified.
        """
        try:
            if block_number is None:
                self.logger.info("Fetching the most recent block")
                block_height = self._make_rpc_call("getblockcount")
            else:
                self.logger.info(f"Fetching block {block_number}")
                block_height = block_number

            # Get block hash and full block data
            block_hash = self._make_rpc_call("getblockhash", [block_height])
            block_data = self._make_rpc_call("getblock", [block_hash, 2])  # Verbosity 2 includes transactions
            
            # Add metadata for processing
            block_data['retrieved_at'] = datetime.utcnow().isoformat()
            block_data['height'] = block_height
            
            return block_data
        except Exception as e:
            self.logger.error(f"Failed to fetch block {block_number}: {e}")
            return None
