-- schema.sql

-- Blocks table
CREATE TABLE IF NOT EXISTS blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    network TEXT NOT NULL,
    block_number INTEGER NOT NULL,
    block_hash TEXT NOT NULL UNIQUE,
    parent_hash TEXT,
    timestamp DATETIME NOT NULL,
    block_data TEXT -- Remove this column in future
);

-- Transactions table
CREATE TABLE IF NOT EXISTS base_evm_transactions (

    block_number INTEGER NOT NULL,
    network TEXT NOT NULL,
    transaction_hash TEXT NOT NULL UNIQUE,
    chain_id INTEGER NOT NULL,
    from_address TEXT NOT NULL,
    to_address TEXT NOT NULL,
    value_wei INTEGER NOT NULL,
    total_gas INTEGER NOT NULL,
    timestamp DATETIME NOT NULL,
    PRIMARY KEY (chain_id, transaction_hash)
);


CREATE TABLE IF NOT EXISTS base_bitcoin_transactions (
    block_number INTEGER NOT NULL,
    transaction_id TEXT NOT NULL UNIQUE,
    version INTEGER NOT NULL,
    value_satoshis REAL NOT NULL,
    timestamp DATETIME NOT NULL,
    fee REAL,
    PRIMARY KEY (transaction_id)
);

-- ABI Table
CREATE TABLE IF NOT EXISTS ethereum_contract_abis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_address TEXT NOT NULL,
    abi TEXT NOT NULL
);

-- Event Signature Table
CREATE TABLE IF NOT EXISTS ethereum_event_signatures (
    signature_hash TEXT PRIMARY KEY,
    event_name TEXT,
    inputs JSONB
);

-- Index for parent-child lookups
CREATE INDEX IF NOT EXISTS idx_parent_child_hash ON blocks (parent_hash, block_hash);

-- Index for network and timestamp queries
CREATE INDEX IF NOT EXISTS idx_network_timestamp ON blocks (network, timestamp);
CREATE INDEX IF NOT EXISTS idx_network_timestamp ON base_evm_transactions (network, timestamp);
CREATE INDEX IF NOT EXISTS idx_network_timestamp ON base_bitcoin_transactions (network, timestamp);

-- Index by block number
CREATE INDEX IF NOT EXISTS idx_block_number ON base_evm_transactions (block_number);
CREATE INDEX IF NOT EXISTS idx_block_number ON base_bitcoin_transactions (block_number);
