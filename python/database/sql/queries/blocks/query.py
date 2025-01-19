QUERY_BLOCKS_BY_TIME = """
    SELECT id, network, block_number, block_hash, parent_hash, timestamp 
    FROM blocks 
    WHERE timestamp BETWEEN %s AND %s
    ORDER BY timestamp ASC;
"""

QUERY_RECENT_BLOCKS = """
    SELECT id, network, block_number, block_hash, parent_hash, timestamp
    FROM blocks 
    ORDER BY block_number DESC 
    LIMIT %s;
"""

QUERY_BLOCKS_BY_NETWORK = """
    SELECT id, network, block_number, block_hash, parent_hash, timestamp
    FROM blocks
    WHERE network = %s
    ORDER BY block_number DESC;
"""

QUERY_RECENT_BLOCKS_BY_NETWORK = """
    SELECT id, network, block_number, block_hash, parent_hash, timestamp
    FROM blocks
    WHERE network = %s
    ORDER BY block_number DESC
    LIMIT %s;
"""
