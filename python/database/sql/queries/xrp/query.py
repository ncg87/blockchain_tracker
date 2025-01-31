QUERY_XRP_TRANSACTIONS = """
    SELECT *
    FROM xrp_transactions
    WHERE block_number = %s
"""

QUERY_RECENT_XRP_TRANSACTIONS = """
    SELECT *
    FROM xrp_transactions
    ORDER BY timestamp DESC
    LIMIT %s
"""