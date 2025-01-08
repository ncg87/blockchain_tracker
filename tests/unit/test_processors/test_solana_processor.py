import pytest
from chains.solana import SolanaProcessor
from unittest.mock import Mock

@pytest.mark.asyncio
async def test_solana_processor_block_processing(test_db):
    """Test Solana block processing."""
    processor = SolanaProcessor(test_db, Mock())
    
    # Test block data
    block = {
        "blockHeight": 1234,
        "blockhash": "test_hash",
        "previousBlockhash": "prev_hash",
        "parentSlot": 1233,
        "blockTime": 1234567890
    }
    
    await processor.process_block(block)
    
    # Verify block was processed and stored
    stored_block = test_db.cursor.execute(
        "SELECT * FROM blocks WHERE network = 'Solana'"
    ).fetchone()
    
    assert stored_block is not None
    assert stored_block[2] == 1234  # block number
    assert stored_block[3] == "test_hash"
