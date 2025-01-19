QUERY_SOLANA_TRANSACTIONS = """
    SELECT *
    FROM base_solana_transactions
    WHERE block_number = %s
"""

QUERY_RECENT_SOLANA_TRANSACTIONS = """
    SELECT *
    FROM base_solana_transactions
    ORDER BY timestamp DESC
    LIMIT %s
"""

