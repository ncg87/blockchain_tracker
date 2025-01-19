def get_network_volume_query(network: str, interval_seconds: int) -> str:
    """Generate SQL query for network volume"""
    if network == 'Bitcoin':
        return f"""
            SELECT COALESCE(SUM(value_satoshis), 0) / 100000000.0 as volume
            FROM base_bitcoin_transactions
            WHERE timestamp >= extract(epoch from now()) - {interval_seconds}
        """
    elif network == 'Solana':
        return f"""
            SELECT COALESCE(SUM(value_lamports), 0) / 1000000000.0 as volume
            FROM base_solana_transactions
            WHERE timestamp >= extract(epoch from now()) - {interval_seconds}
        """
    else:
        return f"""
            SELECT COALESCE(SUM(value_wei), 0) / 1e18 as volume
            FROM base_evm_transactions
            WHERE network = '{network}'
            AND timestamp >= extract(epoch from now()) - {interval_seconds}
        """

def get_all_networks_volume_query(interval_seconds: int) -> str:
    """Generate SQL query for all networks volume"""
    return f"""
        WITH evm_volumes AS (
            SELECT 
                network, 
                CAST(SUM(value_wei) / 1e18 AS NUMERIC(36,18)) as volume
            FROM base_evm_transactions
            WHERE timestamp >= extract(epoch from now()) - {interval_seconds}
            GROUP BY network
        ),
        btc_volume AS (
            SELECT 
                'Bitcoin' as network, 
                CAST(SUM(value_satoshis) / 100000000.0 AS NUMERIC(36,18)) as volume
            FROM base_bitcoin_transactions
            WHERE timestamp >= extract(epoch from now()) - {interval_seconds}
        ),
        solana_volume AS (
            SELECT 
                'Solana' as network,
                CAST(SUM(value_lamports) / 1000000000.0 AS NUMERIC(36,18)) as volume
            FROM base_solana_transactions
            WHERE timestamp >= extract(epoch from now()) - {interval_seconds}
        )
        SELECT network, volume
        FROM (
            SELECT * FROM evm_volumes
            UNION ALL
            SELECT * FROM btc_volume
            UNION ALL
            SELECT * FROM solana_volume
        ) all_volumes
        ORDER BY network
    """