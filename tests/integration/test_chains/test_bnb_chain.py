import pytest
from chains.bnb import BNBPipeline, BNBProcessor, BNBQuerier
import json
from unittest.mock import AsyncMock


@pytest.mark.asyncio
class TestBNBIntegration:
    async def test_bnb_pipeline_flow(self, test_db, mock_websocket, monkeypatch):
        """Test complete BNB pipeline flow."""
        # Mock websocket connection
        monkeypatch.setattr('websockets.connect', AsyncMock(return_value=mock_websocket))
        
        pipeline = BNBPipeline(test_db)
        
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
            "proofOfAuthorityData": "0x",
            "blobGasUsed": "0x1",
            "excessBlobGas": "0x1"
        }
        
        mock_websocket.recv.return_value = json.dumps({
            "result": mock_block
        })
        
        # Run pipeline for a short duration
        await pipeline.run(duration=1)
        
        # Verify block was stored
        stored_block = test_db.cursor.execute(
            "SELECT * FROM blocks WHERE network = 'BNB'"
        ).fetchone()
        
        assert stored_block is not None
        assert stored_block[1] == "BNB"