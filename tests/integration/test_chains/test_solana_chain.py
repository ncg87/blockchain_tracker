import pytest
from chains.solana import SolanaPipeline, SolanaProcessor, SolanaQuerier
from unittest.mock import Mock
import json

@pytest.mark.asyncio
class TestSolanaIntegration:
    async def test_solana_pipeline_flow(self, test_db, mock_websocket, monkeypatch):
        """Test complete Solana pipeline flow."""
        pipeline = SolanaPipeline(test_db)
        
        # Mock block data
        mock_block = {
            "previousBlockhash": "prev_hash",
            "blockhash": "test_hash",
            "parentSlot": 1234,
            "blockTime": 1234567890,
            "blockHeight": 5678,
            "transactions": []
        }
        
        # Mock RPC response
        monkeypatch.setattr(
            pipeline.querier.client,
            'get_block',
            Mock(return_value=mock_block)
        )
        
        # Run pipeline for a short duration
        await pipeline.run(duration=1)
        
        # Verify block was stored
        stored_block = test_db.cursor.execute(
            "SELECT * FROM blocks WHERE network = 'Solana'"
        ).fetchone()
        
        assert stored_block is not None
        assert stored_block[1] == "Solana"