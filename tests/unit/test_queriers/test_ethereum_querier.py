import pytest
from chains.ethereum import EthereumQuerier
from web3 import Web3
from hexbytes import HexBytes
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_ethereum_block_fetching(monkeypatch):
    """Test Ethereum block fetching."""
    querier = EthereumQuerier()
    
    # Mock Web3 response
    mock_block = {
        "number": 1,
        "hash": HexBytes("0xblock_hash"),
        "parentHash": HexBytes("0xparent_hash"),
        "timestamp": 1234567890
    }
    
    monkeypatch.setattr(
        querier.w3.eth,
        'get_block',
        Mock(return_value=mock_block)
    )
    
    block = await querier.get_block(1)
    assert block["number"] == 1
    assert block["hash"].hex() == "0xblock_hash"

@pytest.mark.asyncio
async def test_ethereum_block_streaming(monkeypatch, mock_websocket):
    """Test Ethereum block streaming."""
    querier = EthereumQuerier()
    
    # Mock WebSocket
    monkeypatch.setattr(
        querier.ws,
        'run',
        AsyncMock(return_value=[{"blockNumber": 1}])
    )
    
    blocks = []
    async for block in querier.stream_blocks(duration=1):
        blocks.append(block)
    
    assert len(blocks) > 0
