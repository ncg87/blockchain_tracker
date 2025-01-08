import pytest
from chains.bitcoin import BitcoinPipeline, BitcoinProcessor, BitcoinQuerier
from unittest.mock import AsyncMock


@pytest.mark.asyncio
class TestBitcoinIntegration:
    async def test_bitcoin_pipeline_flow(self, test_db, monkeypatch):
        """Test complete Bitcoin pipeline flow."""
        pipeline = BitcoinPipeline(test_db)
        
        # Mock RPC response
        mock_block = {
            "hash": "test_hash",
            "height": 1,
            "version": 1,
            "merkleroot": "test_merkle",
            "time": 1234567890,
            "nonce": 12345,
            "bits": "test_bits",
            "previousblockhash": "prev_hash"
        }
        
        # Mock RPC call
        monkeypatch.setattr(
            pipeline.querier,
            '_make_rpc_call',
            AsyncMock(return_value=mock_block)
        )
        
        # Run pipeline for a short duration
        await pipeline.run(duration=1)
        
        # Verify block was stored
        stored_block = test_db.cursor.execute(
            "SELECT * FROM blocks WHERE network = 'Bitcoin'"
        ).fetchone()
        
        assert stored_block is not None
        assert stored_block[1] == "Bitcoin"