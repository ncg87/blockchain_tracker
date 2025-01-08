import pytest
from database import QueryOperations
from datetime import datetime, timedelta
from database import InsertOperations

def test_query_blocks_by_time(test_db, sample_block_data):
    """Test querying blocks by time range."""
    query_ops = QueryOperations(test_db)
    insert_ops = InsertOperations(test_db)
    
    # Insert test block
    insert_ops.insert_block(sample_block_data)
    
    # Query within time range
    start_time = datetime.strptime("2025-01-07 00:00:00", "%Y-%m-%d %H:%M:%S")
    end_time = datetime.strptime("2025-01-09 00:00:00", "%Y-%m-%d %H:%M:%S")
    
    blocks = query_ops.query_blocks_by_time(start_time, end_time)
    assert len(blocks) == 1
    assert blocks[0][1] == sample_block_data["network"]

def test_query_by_network(test_db, sample_block_data):
    """Test querying blocks by network."""
    query_ops = QueryOperations(test_db)
    insert_ops = InsertOperations(test_db)
    
    # Insert test block
    insert_ops.insert_block(sample_block_data)
    
    # Query by network
    blocks = query_ops.query_by_network(sample_block_data["network"])
    assert len(blocks) == 1
    assert blocks[0][1] == sample_block_data["network"]
    
    # Query with specific block number
    blocks = query_ops.query_by_network(
        sample_block_data["network"], 
        sample_block_data["block_number"]
    )
    assert len(blocks) == 1
    assert blocks[0][2] == sample_block_data["block_number"]