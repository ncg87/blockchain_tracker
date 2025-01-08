import pytest
from chains.bitcoin import BitcoinProcessor
from unittest.mock import Mock

@pytest.mark.asyncio
async def test_bitcoin_processor_block_processing(test_db):
    """Test Bitcoin block processing."""
    processor = BitcoinProcessor(test_db, Mock())
    
    # Test block data
    block = {
        "hash": "test_hash",
        "height": 1,
        "version": 1,
        "merkleroot": "test_merkle",
        "time": 1234567890,
        "nonce": 12345,
        "bits": "test_bits",
        "previousblockhash": "prev_hash",
        "chainwork": "chainwork",
        "weight": 1000,
        "size": 1000,
        "nTx": 10
    }
    
    await processor.process_block(block)
    
    # Verify block was processed and stored
    stored_block = test_db.cursor.execute(
        "SELECT * FROM blocks WHERE network = 'Bitcoin'"
    ).fetchone()
    
    assert stored_block is not None
    assert stored_block[2] == 1  # block number
    assert stored_block[3] == "test_hash"