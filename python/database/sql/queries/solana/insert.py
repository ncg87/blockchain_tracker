INSERT_SOLANA_TRANSACTIONS = """
    INSERT INTO solana_transactions 
    (block_number, signature, amount, fee, account_key, timestamp)
    VALUES %s
    ON CONFLICT (timestamp, signature) DO NOTHING
"""