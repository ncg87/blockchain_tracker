import pytest
from database import InsertOperations
from datetime import datetime


def test_insert_block(test_db):
    """Test block insertion."""
    insert_ops = InsertOperations(test_db)
    
    block_data = {
        "network": "test_network",
        "block_number": 1,
        "block_hash": "0xtest",
        "parent_hash": "0xparent",
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "block_data": '{"test": "data"}'
    }
    
    insert_ops.insert_block(block_data)
    
    # Verify insertion
    cursor = test_db.cursor
    result = cursor.execute(
        "SELECT * FROM blocks WHERE block_hash = ?",
        ("0xtest",)
    ).fetchone()
    
    assert result is not None
    assert result[1] == "test_network"
    assert result[2] == 1