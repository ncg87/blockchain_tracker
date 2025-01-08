import pytest
from chains.xrp import XRPPipeline, XRPProcessor, XRPQuerier
import json
from unittest.mock import AsyncMock

@pytest.mark.asyncio
class TestXRPIntegration:
    async def test_xrp_pipeline_flow(self, test_db, mock_websocket, monkeypatch):
        """Test complete XRP pipeline flow."""
        # Mock websocket connection
        monkeypatch.setattr('websockets.connect', AsyncMock(return_value=mock_websocket))
        
        pipeline = XRPPipeline(test_db)
        
        # Mock ledger data
        mock_ledger = {
            "ledger": {
                "ledger_index": 1234,
                "ledger_hash": "test_hash",
                "parent_hash": "parent_hash",
                "total_coins": "100000000",
                "close_time": 1234567890,
                "account_hash": "account_hash"
            }
        }
        
        mock_websocket.recv.return_value = json.dumps({
            "type": "ledgerClosed",
            "ledger_index": 1234,
            "ledger_hash": "test_hash"
        })
        
        # Mock ledger fetch
        monkeypatch.setattr(
            pipeline.querier,
            'get_block',
            AsyncMock(return_value=mock_ledger)
        )
        
        # Run pipeline for a short duration
        await pipeline.run(duration=1)
        
        # Verify ledger was stored
        stored_block = test_db.cursor.execute(
            "SELECT * FROM blocks WHERE network = 'XRP'"
        ).fetchone()
        
        assert stored_block is not None
        assert stored_block[1] == "XRP"