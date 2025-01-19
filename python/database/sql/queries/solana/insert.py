INSERT_SOLANA_TRANSACTIONS = """
    INSERT INTO base_solana_transactions 
    (block_number, signature, value_lamports, fee_lamports, account_key, timestamp)
    VALUES %s
    ON CONFLICT (timestamp, signature) DO NOTHING
"""