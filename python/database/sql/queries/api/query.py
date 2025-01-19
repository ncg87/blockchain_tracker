def get_network_volume_query(network: str, interval_seconds: int) -> str:
    """Generate SQL query for EVM network volume"""
    if network == 'Bitcoin':
        return f"""
            SELECT COALESCE(SUM(value_satoshis), 0) as volume
            FROM base_bitcoin_transactions
            WHERE timestamp >= extract(epoch from now()) - {interval_seconds}
        """
    else:
        return f"""
            SELECT COALESCE(SUM(value_wei), 0) as volume
            FROM base_evm_transactions
            WHERE network = '{network}'
            AND timestamp >= extract(epoch from now()) - {interval_seconds}
        """

def get_all_networks_volume_query(interval_seconds: int) -> str:
    """Generate SQL query for all networks volume"""
    return f"""
        WITH evm_volumes AS (
            SELECT network, COALESCE(SUM(value_wei), 0) as volume
            FROM base_evm_transactions
            WHERE timestamp >= extract(epoch from now()) - {interval_seconds}
            GROUP BY network
        ),
        btc_volume AS (
            SELECT 'Bitcoin' as network, COALESCE(SUM(value_satoshis), 0) as volume
            FROM base_bitcoin_transactions
            WHERE timestamp >= extract(epoch from now()) - {interval_seconds}
        )
        SELECT network, volume
        FROM (
            SELECT * FROM evm_volumes
            UNION ALL
            SELECT * FROM btc_volume
        ) all_volumes
        ORDER BY network
    """