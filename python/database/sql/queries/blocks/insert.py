INSERT_BLOCK = """
    INSERT INTO blocks (network, block_number, block_hash, parent_hash, timestamp)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (network, block_number, id) DO NOTHING
""" 