import pytest
from chains.bitcoin import BitcoinQuerier
from unittest.mock import patch

@pytest.mark.asyncio
async def test_bitcoin_rpc_call():
    """Test Bitcoin RPC calls."""
    querier = BitcoinQuerier()
    
    # Mock RPC response
    mock_response = {
        "result": {
            "chain": "main",
            "blocks": 1234,
            "headers": 1234
        }
    }
    
    with patch('requests.post') as mock_post:
        mock_post.return_value.json.return_value = mock_response
        
        info = await querier._make_rpc_call("getblockchaininfo")
        assert info["chain"] == "main"
        assert info["blocks"] == 1234
