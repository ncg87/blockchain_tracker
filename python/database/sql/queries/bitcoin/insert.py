INSERT_BITCOIN_TRANSACTIONS = """
    INSERT INTO base_bitcoin_transactions 
    (block_number, transaction_id, version, value_satoshis, timestamp, fee)
    VALUES %s
    ON CONFLICT (timestamp, transaction_id) DO NOTHING
"""