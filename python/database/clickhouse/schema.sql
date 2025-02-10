CREATE TABLE IF NOT EXISTS blockchain_db.dex_swaps
(
    timestamp UInt32,  -- Unix epoch time
    chain String,  -- Blockchain network (Ethereum, BSC, Solana, etc.)
    dex String,  -- DEX identifier (Uniswap, SushiSwap, etc.)
    factory_id String,  -- Factory contract address
    from_coin_symbol String,  -- Token symbol being swapped from
    from_coin_address String,  -- Token contract address
    to_coin_symbol String,  -- Token symbol being swapped to
    to_coin_address String,  -- Token contract address
    price_from Float64  -- Swap price
) ENGINE = MergeTree()
ORDER BY (timestamp, chain, dex, factory_id, from_coin_address, to_coin_address);
