def get_network_volume_query(network: str, interval_seconds: int) -> str:
    """Generate SQL query for network volume"""
    if network == 'Bitcoin':
        return f"""
            SELECT COALESCE(SUM(value_satoshis), 0) as volume
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
                COALESCE(CAST(SUM(value_wei) / 1e18 AS NUMERIC(36,18)), 0) as volume
            FROM base_evm_transactions
            WHERE timestamp >= extract(epoch from now()) - {interval_seconds}
            AND network IN ('Ethereum', 'BNB', 'Base')
            GROUP BY network
        ),
        btc_volume AS (
            SELECT 
                'Bitcoin' as network, 
                COALESCE(CAST(SUM(value_satoshis) AS NUMERIC(36,18)), 0) as volume
            FROM base_bitcoin_transactions
            WHERE timestamp >= extract(epoch from now()) - {interval_seconds}
        ),
        solana_volume AS (
            SELECT 
                'Solana' as network,
                COALESCE(CAST(SUM(value_lamports) / 1000000000.0 AS NUMERIC(36,18)), 0) as volume
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

def get_network_fees_query(network: str, interval_seconds: int) -> str:
    """Generate SQL query for network fees"""
    if network in ['Ethereum', 'BNB', 'Base']:
        return f"""
            SELECT CAST(SUM(total_gas) AS NUMERIC(36,18)) as total_fees
            FROM base_evm_transactions
            WHERE network = '{network}'
            AND timestamp >= extract(epoch from now()) - {interval_seconds}
        """
    elif network == 'Bitcoin':
        return f"""
            SELECT CAST(SUM(fee) AS NUMERIC(36,18)) as total_fees
            FROM base_bitcoin_transactions
            WHERE timestamp >= extract(epoch from now()) - {interval_seconds}
        """
    elif network == 'Solana':
        return f"""
            SELECT CAST(SUM(fee_lamports) / 1000000000.0 AS NUMERIC(36,18)) as total_fees
            FROM base_solana_transactions
            WHERE timestamp >= extract(epoch from now()) - {interval_seconds}
        """
    return ""

def get_all_networks_fees_query(interval_seconds: int) -> str:
    """Generate SQL query for all networks fees"""
    return f"""
        WITH evm_fees AS (
            SELECT 
                network, 
                COALESCE(CAST(SUM(total_gas) / 1e18 AS NUMERIC(36,18)), 0) as total_fees
            FROM base_evm_transactions
            WHERE timestamp >= extract(epoch from now()) - {interval_seconds}
            AND network IN ('Ethereum', 'BNB', 'Base')
            GROUP BY network
        ),
        btc_fees AS (
            SELECT 
                'Bitcoin' as network, 
                COALESCE(CAST(SUM(fee) AS NUMERIC(36,18)), 0) as total_fees
            FROM base_bitcoin_transactions
            WHERE timestamp >= extract(epoch from now()) - {interval_seconds}
        ),
        solana_fees AS (
            SELECT 
                'Solana' as network,
                COALESCE(CAST(SUM(fee_lamports) / 1000000000.0 AS NUMERIC(36,18)), 0) as total_fees
            FROM base_solana_transactions
            WHERE timestamp >= extract(epoch from now()) - {interval_seconds}
        )
        SELECT network, total_fees
        FROM (
            SELECT * FROM evm_fees
            UNION ALL
            SELECT * FROM btc_fees
            UNION ALL
            SELECT * FROM solana_fees
        ) all_fees
        ORDER BY network
    """

def get_network_tx_count_query(network: str, interval_seconds: int) -> str:
    """Generate SQL query for network transaction count"""
    if network in ['Ethereum', 'BNB', 'Base']:
        return f"""
            SELECT COUNT(*) as tx_count
            FROM base_evm_transactions
            WHERE network = '{network}'
            AND timestamp >= extract(epoch from now()) - {interval_seconds}
        """
    elif network == 'Bitcoin':
        return f"""
            SELECT COUNT(*) as tx_count
            FROM base_bitcoin_transactions
            WHERE timestamp >= extract(epoch from now()) - {interval_seconds}
        """
    elif network == 'Solana':
        return f"""
            SELECT COUNT(*) as tx_count
            FROM base_solana_transactions
            WHERE timestamp >= extract(epoch from now()) - {interval_seconds}
        """
    return ""

def get_all_networks_tx_count_query(interval_seconds: int) -> str:
    """Generate SQL query for all networks transaction count"""
    return f"""
        WITH time_bounds AS (
            SELECT 
                extract(epoch from now()) as current_time,
                extract(epoch from now()) - {interval_seconds} as start_time
        ),
        evm_counts AS (
            SELECT 
                network, 
                COUNT(*) as tx_count,
                MIN(timestamp) as earliest_tx,
                MAX(timestamp) as latest_tx
            FROM base_evm_transactions
            WHERE timestamp >= extract(epoch from now()) - {interval_seconds}
            AND network IN ('Ethereum', 'BNB', 'Base')
            GROUP BY network
        ),
        btc_count AS (
            SELECT 
                'Bitcoin' as network, 
                COUNT(*) as tx_count,
                MIN(timestamp) as earliest_tx,
                MAX(timestamp) as latest_tx
            FROM base_bitcoin_transactions
            WHERE timestamp >= extract(epoch from now()) - {interval_seconds}
        ),
        solana_count AS (
            SELECT 
                'Solana' as network,
                COUNT(*) as tx_count,
                MIN(timestamp) as earliest_tx,
                MAX(timestamp) as latest_tx
            FROM base_solana_transactions
            WHERE timestamp >= extract(epoch from now()) - {interval_seconds}
        )
        SELECT 
            a.network, 
            a.tx_count,
            a.earliest_tx,
            a.latest_tx,
            t.current_time,
            t.start_time
        FROM (
            SELECT * FROM evm_counts
            UNION ALL
            SELECT * FROM btc_count
            UNION ALL
            SELECT * FROM solana_count
        ) a
        CROSS JOIN time_bounds t
        ORDER BY network
    """

def get_network_historical_data_query(network: str, interval_seconds: int, points: int) -> str:
    """Generate SQL query for historical network data with specified intervals"""
    if network in ['Ethereum', 'BNB', 'Base']:
        return f"""
            WITH time_series AS (
                SELECT generate_series(
                    date_trunc('hour', now()) - interval '{points} hours',
                    date_trunc('hour', now()),
                    interval '1 hour'
                ) AS interval_start
            )
            SELECT 
                EXTRACT(EPOCH FROM ts.interval_start) as timestamp,
                COALESCE(SUM(value_wei) / 1e18, 0) as volume,
                COALESCE(SUM(total_gas)/ 1e18, 0) as fees,
                COUNT(*) as transactions
            FROM time_series ts
            LEFT JOIN base_evm_transactions tx ON 
                tx.timestamp >= EXTRACT(EPOCH FROM ts.interval_start) AND
                tx.timestamp < EXTRACT(EPOCH FROM ts.interval_start + interval '1 hour') AND
                tx.network = '{network}'
            GROUP BY ts.interval_start
            ORDER BY ts.interval_start DESC
        """
    elif network == 'Bitcoin':
        return f"""
            WITH time_series AS (
                SELECT generate_series(
                    date_trunc('hour', now()) - interval '{points} hours',
                    date_trunc('hour', now()),
                    interval '1 hour'
                ) AS interval_start
            )
            SELECT 
                EXTRACT(EPOCH FROM ts.interval_start) as timestamp,
                COALESCE(SUM(value_satoshis) / 100000000.0, 0) as volume,
                COALESCE(SUM(fee), 0) as fees,
                COUNT(*) as transactions
            FROM time_series ts
            LEFT JOIN base_bitcoin_transactions tx ON 
                tx.timestamp >= EXTRACT(EPOCH FROM ts.interval_start) AND
                tx.timestamp < EXTRACT(EPOCH FROM ts.interval_start + interval '1 hour')
            GROUP BY ts.interval_start
            ORDER BY ts.interval_start DESC
        """
    elif network == 'Solana':
        return f"""
            WITH time_series AS (
                SELECT generate_series(
                    date_trunc('hour', now()) - interval '{points} hours',
                    date_trunc('hour', now()),
                    interval '1 hour'
                ) AS interval_start
            )
            SELECT 
                EXTRACT(EPOCH FROM ts.interval_start) as timestamp,
                COALESCE(SUM(value_lamports) / 1000000000.0, 0) as volume,
                COALESCE(SUM(fee_lamports) / 1000000000.0, 0) as fees,
                COUNT(*) as transactions
            FROM time_series ts
            LEFT JOIN base_solana_transactions tx ON 
                tx.timestamp >= EXTRACT(EPOCH FROM ts.interval_start) AND
                tx.timestamp < EXTRACT(EPOCH FROM ts.interval_start + interval '1 hour')
            GROUP BY ts.interval_start
            ORDER BY ts.interval_start DESC
        """
    return ""
