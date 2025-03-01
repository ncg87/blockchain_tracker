CREATE TABLE IF NOT EXISTS blockchain_db.block_timestamps
(
    chain String,
    timestamp UInt32,
    block_number UInt64
) ENGINE = MergeTree()
ORDER BY (chain, timestamp, block_number);

CREATE TABLE IF NOT EXISTS blockchain_db.dex_prices
(
    chain LowCardinality(String),
    timestamp UInt32,
    log_index UInt32,
    factory_id String,
    contract_id String,
    from_coin_symbol LowCardinality(String),
    from_coin_address String,
    to_coin_symbol LowCardinality(String),
    to_coin_address String,
    price_from Decimal(38, 18),
    reserve_from Decimal(42,8),
    reserve_to Decimal(42,8),
    fees Decimal(10, 4)
) ENGINE = MergeTree()
PARTITION BY chain
ORDER BY (chain, factory_id, timestamp, log_index, contract_id, from_coin_address, to_coin_address);

CREATE MATERIALIZED VIEW IF NOT EXISTS blockchain_db.dex_prices_filled
ENGINE = MergeTree()
PARTITION BY chain
ORDER BY (chain, factory_id, contract_id, from_coin_address, to_coin_address, timestamp)
POPULATE
AS 
WITH 
    distinct_pairs AS (
        SELECT DISTINCT 
            chain,
            factory_id,
            contract_id,
            from_coin_symbol,
            from_coin_address,
            to_coin_symbol,
            to_coin_address
        FROM blockchain_db.dex_prices
        WHERE chain = 'base'
    )
SELECT 
    bt.timestamp as timestamp,
    distinct_pairs.chain as chain,
    distinct_pairs.factory_id as factory_id,
    distinct_pairs.contract_id as contract_id,
    distinct_pairs.from_coin_symbol as from_coin_symbol,
    distinct_pairs.from_coin_address as from_coin_address,
    distinct_pairs.to_coin_symbol as to_coin_symbol,
    distinct_pairs.to_coin_address as to_coin_address,
    CAST(argMaxIf(dp_actual.price_from, (dp_actual.timestamp, dp_actual.log_index), dp_actual.timestamp <= bt.timestamp) AS Decimal(18,8)) AS price_from,
    CAST(argMaxIf(dp_actual.reserve_from, (dp_actual.timestamp, dp_actual.log_index), dp_actual.timestamp <= bt.timestamp) AS Decimal(42,8)) AS reserve_from,
    CAST(argMaxIf(dp_actual.reserve_to, (dp_actual.timestamp, dp_actual.log_index), dp_actual.timestamp <= bt.timestamp) AS Decimal(42,8)) AS reserve_to,
    argMaxIf(dp_actual.fees, (dp_actual.timestamp, dp_actual.log_index), dp_actual.timestamp <= bt.timestamp) AS fees
FROM blockchain_db.block_timestamps bt
CROSS JOIN distinct_pairs
LEFT JOIN blockchain_db.dex_prices dp_actual
    ON dp_actual.chain = distinct_pairs.chain
    AND dp_actual.contract_id = distinct_pairs.contract_id
    AND dp_actual.from_coin_address = distinct_pairs.from_coin_address
    AND dp_actual.to_coin_address = distinct_pairs.to_coin_address
GROUP BY 
    bt.timestamp,
    distinct_pairs.chain,
    distinct_pairs.factory_id,
    distinct_pairs.contract_id,
    distinct_pairs.from_coin_symbol,
    distinct_pairs.from_coin_address,
    distinct_pairs.to_coin_symbol,
    distinct_pairs.to_coin_address
HAVING price_from IS NOT NULL;