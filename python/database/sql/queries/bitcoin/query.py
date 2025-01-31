QUERY_BITCOIN_TRANSACTIONS = """
    SELECT *
    FROM bitcoin_transactions 
    WHERE block_number = %s;
"""

QUERY_RECENT_BITCOIN_TRANSACTIONS = """
    SELECT *
    FROM bitcoin_transactions 
    ORDER BY timestamp DESC
    LIMIT %s;
"""