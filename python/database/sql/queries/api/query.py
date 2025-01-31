def get_swaps_by_chain(chain: str, seconds_ago: int) -> str:
    return f"""
    SELECT *
    FROM evm_swaps
    WHERE 
        chain = '{chain}'
        AND timestamp BETWEEN 
            EXTRACT(EPOCH FROM NOW())::integer - {seconds_ago}
            AND EXTRACT(EPOCH FROM NOW())::integer
    ORDER BY timestamp DESC;
    """
   
def get_swaps(seconds_ago: int) -> str:
    return f"""
    SELECT *
    FROM evm_swaps
    WHERE timestamp BETWEEN 
        EXTRACT(EPOCH FROM NOW())::integer - {seconds_ago}
        AND EXTRACT(EPOCH FROM NOW())::integer
    ORDER BY timestamp DESC;
    """

