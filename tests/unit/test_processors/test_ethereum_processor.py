import pytest
from chains.ethereum import EthereumProcessor
from hexbytes import HexBytes
from unittest.mock import Mock

@pytest.mark.asyncio
async def test_ethereum_processor_block_processing(test_db):
    """Test Ethereum block processing."""
    processor = EthereumProcessor(test_db, Mock())
    
    # Test block data
    block = {
        "number": HexBytes("0x1"),
        "hash": HexBytes("0xblock_hash"),
        "parentHash": HexBytes("0xparent_hash"),
        "timestamp": HexBytes("0x60d"),
        "miner": "0xminer",
        "gasLimit": HexBytes("0x1"),
        "gasUsed": HexBytes("0x1"),
        "baseFeePerGas": HexBytes("0x1"),
        "size": HexBytes("0x1"),
        "extraData": HexBytes("0x"),
        "blobGasUsed": HexBytes("0x1"),
        "excessBlobGas": HexBytes("0x1")
    }
    
    await processor.process_block(block)
    
    # Verify block was processed and stored
    stored_block = test_db.cursor.execute(
        "SELECT * FROM blocks WHERE network = 'Ethereum'"
    ).fetchone()
    
    assert stored_block is not None
    assert stored_block[2] == 1  # block number
    assert stored_block[3] == "0xblock_hash"
