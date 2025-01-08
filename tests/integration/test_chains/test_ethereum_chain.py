import pytest
from chains.ethereum import EthereumPipeline, EthereumProcessor, EthereumQuerier
from unittest.mock import AsyncMock
import json

@pytest.mark.asyncio
class TestEthereumIntegration:
    async def test_ethereum_pipeline_flow(self, test_db, mock_websocket, monkeypatch):
        """Test complete Ethereum pipeline flow."""
        # Mock websocket connection
        monkeypatch.setattr('websockets.connect', AsyncMock(return_value=mock_websocket))
        
        # Setup pipeline
        pipeline = EthereumPipeline(test_db)
        
        # Mock block data
        mock_block = {
            "number": "0x1",
            "hash": "0xblock_hash",
            "parentHash": "0xparent_hash",
            "timestamp": "0x60d",
            "transactions": [],
            "miner": "0xminer",
            "gasLimit": "0x1",
            "gasUsed": "0x1",
            "baseFeePerGas": "0x1",
            "size": "0x1",
            "extraData": "0x",
            "blobGasUsed": "0x1",
            "excessBlobGas": "0x1"
        }
        
        # Mock websocket response
        mock_websocket.recv.return_value = json.dumps({
            "result": mock_block
        })
        
        # Run pipeline for a short duration
        await pipeline.run(duration=1)
        
        # Verify block was stored
        stored_block = test_db.cursor.execute(
            "SELECT * FROM blocks WHERE network = 'Ethereum'"
        ).fetchone()
        
        assert stored_block is not None
        assert stored_block[1] == "Ethereum"