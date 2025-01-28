INSERT_BLOCK = """
    INSERT INTO blocks (chain, block_number, block_hash, parent_hash, timestamp)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (chain, block_hash) DO NOTHING
""" 