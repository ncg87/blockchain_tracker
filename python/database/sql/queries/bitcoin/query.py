QUERY_BITCOIN_TRANSACTIONS = """
    SELECT block_number, transaction_id, version, 
           value_satoshis, timestamp, fee
    FROM base_bitcoin_transactions 
    WHERE block_number = %s;
"""

QUERY_RECENT_BITCOIN_TRANSACTIONS = """
    SELECT block_number, transaction_id, version, 
           value_satoshis, timestamp, fee
    FROM base_bitcoin_transactions 
    ORDER BY timestamp DESC
    LIMIT %s;
"""