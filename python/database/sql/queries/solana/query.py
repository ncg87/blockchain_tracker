QUERY_SOLANA_TRANSACTIONS = """
    SELECT *
    FROM solana_transactions
    WHERE block_number = %s
"""

QUERY_RECENT_SOLANA_TRANSACTIONS = """
    SELECT *
    FROM solana_transactions
    ORDER BY timestamp DESC
    LIMIT %s
"""

