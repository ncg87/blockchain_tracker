INSERT_XRP_TRANSACTIONS = """
    INSERT INTO base_xrp_transactions 
    (block_number, transaction_hash, account, type, fee, timestamp)
    VALUES %s
    ON CONFLICT (timestamp, transaction_hash) DO NOTHING
"""