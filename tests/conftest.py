import pytest
import os
import sqlite3
from pathlib import Path
from database import Database
import asyncio
import json
from unittest.mock import Mock, AsyncMock

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test function."""
    # Use in-memory SQLite database for testing
    db_path = ":memory:"
    db = Database(db_path)
    
    yield db
    
    db.close()

@pytest.fixture
def mock_websocket():
    """Create a mock websocket for testing."""
    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()
    mock_ws.recv = AsyncMock(return_value=json.dumps({
        "type": "test",
        "data": "test_data"
    }))
    mock_ws.close = AsyncMock()
    return mock_ws

@pytest.fixture
def sample_block_data():
    """Provide sample block data for testing."""
    return {
        "network": "test_network",
        "block_number": 12345,
        "block_hash": "0xtest_hash",
        "parent_hash": "0xparent_hash",
        "timestamp": "2025-01-08 00:00:00",
        "block_data": json.dumps({"test": "data"})
    }