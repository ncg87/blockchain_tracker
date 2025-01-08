import pytest
from chains.base_models import BaseWebSocketHandler
import asyncio
import json
from unittest.mock import AsyncMock

class TestWebSocketHandler(BaseWebSocketHandler):
    def get_subscription_message(self):
        return {"type": "subscribe"}
    
    def parse_message(self, message):
        return message
    
    async def fetch_full_data(self, parsed_message):
        return parsed_message

@pytest.mark.asyncio
async def test_websocket_handler_initialization():
    """Test WebSocket handler initialization."""
    handler = TestWebSocketHandler("Test", "ws://test.com")
    assert handler.network == "Test"
    assert handler.websocket_url == "ws://test.com"
    assert handler.running is False

@pytest.mark.asyncio
async def test_websocket_connection(mock_websocket, monkeypatch):
    """Test WebSocket connection and subscription."""
    monkeypatch.setattr('websockets.connect', AsyncMock(return_value=mock_websocket))
    
    handler = TestWebSocketHandler("Test", "ws://test.com")
    await handler.connect()
    await handler.subscribe()
    
    # Verify subscription message was sent
    mock_websocket.send.assert_called_once()
    subscription_msg = json.loads(mock_websocket.send.call_args[0][0])
    assert subscription_msg["type"] == "subscribe"