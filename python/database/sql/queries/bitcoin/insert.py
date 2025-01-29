INSERT_BITCOIN_TRANSACTIONS = """
    INSERT INTO bitcoin_transactions 
    (block_number, transaction_hash, version, amount, timestamp, fee)
    VALUES %s
    ON CONFLICT (timestamp, transaction_hash) DO NOTHING
"""