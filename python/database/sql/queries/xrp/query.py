QUERY_XRP_TRANSACTIONS = """
    SELECT *
    FROM base_xrp_transactions
    WHERE block_number = %s
"""

QUERY_RECENT_XRP_TRANSACTIONS = """
    SELECT *
    FROM base_xrp_transactions
    ORDER BY timestamp DESC
    LIMIT %s
"""