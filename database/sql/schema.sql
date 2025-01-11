
-- Blocks table
CREATE TABLE IF NOT EXISTS blocks (
    id INTEGER PRIMARY KEY, -- SQLite auto-increments INTEGER PRIMARY KEY automatically
    network VARCHAR(20) NOT NULL,
    block_number BIGINT NOT NULL,
    block_hash CHAR(64) NOT NULL UNIQUE,
    parent_hash CHAR(64),
    timestamp BIGINT NOT NULL -- Unix timestamp
);

CREATE INDEX IF NOT EXISTS idx_blocks_block_number_network ON blocks (block_number, network);

-- EVM type Transactions table
CREATE TABLE IF NOT EXISTS base_evm_transactions (
    block_number BIGINT NOT NULL,
    network VARCHAR(20) NOT NULL,
    transaction_hash CHAR(64) NOT NULL UNIQUE,
    chain_id SMALLINT NOT NULL,
    from_address CHAR(42) NOT NULL,
    to_address CHAR(42),
    value_wei DECIMAL(38, 0) NOT NULL,
    total_gas BIGINT NOT NULL,
    timestamp BIGINT NOT NULL, -- Unix timestamp
    PRIMARY KEY (transaction_hash)
);

CREATE INDEX IF NOT EXISTS idx_evm_transactions_block_network ON base_evm_transactions (block_number, network);
CREATE INDEX IF NOT EXISTS idx_evm_transactions_from_address ON base_evm_transactions (from_address);
CREATE INDEX IF NOT EXISTS idx_evm_transactions_to_address ON base_evm_transactions (to_address);

-- Bitcoin Transactions table
CREATE TABLE IF NOT EXISTS base_bitcoin_transactions (
    block_number BIGINT NOT NULL,
    transaction_id CHAR(64) NOT NULL UNIQUE,
    version SMALLINT NOT NULL,
    value_satoshis DECIMAL(20, 0) NOT NULL,
    timestamp BIGINT NOT NULL, -- Unix timestamp
    fee DECIMAL(16, 8) NOT NULL,
    PRIMARY KEY (transaction_id)
);

CREATE INDEX IF NOT EXISTS idx_bitcoin_transactions_block_number ON base_bitcoin_transactions (block_number);
CREATE INDEX IF NOT EXISTS idx_bitcoin_transactions_timestamp ON base_bitcoin_transactions (timestamp);

-- XRP Transactions table
CREATE TABLE IF NOT EXISTS base_xrp_transactions (
    block_number BIGINT NOT NULL,
    transaction_hash CHAR(64) NOT NULL UNIQUE,
    account CHAR(35) NOT NULL,
    type VARCHAR(20) NOT NULL,
    fee BIGINT NOT NULL,
    timestamp BIGINT NOT NULL, -- Unix timestamp
    PRIMARY KEY (transaction_hash)
);

CREATE INDEX IF NOT EXISTS idx_xrp_transactions_block_number ON base_xrp_transactions (block_number);
CREATE INDEX IF NOT EXISTS idx_xrp_transactions_account ON base_xrp_transactions (account);
CREATE INDEX IF NOT EXISTS idx_xrp_transactions_timestamp ON base_xrp_transactions (timestamp);

-- Ethereum Contract ABIs
CREATE TABLE IF NOT EXISTS ethereum_contract_abis (
    id INTEGER PRIMARY KEY, -- SQLite auto-increments INTEGER PRIMARY KEY automatically
    contract_address CHAR(42) NOT NULL UNIQUE
);

-- Ethereum Event Signatures
CREATE TABLE IF NOT EXISTS ethereum_event_signatures (
    signature_hash CHAR(64) NOT NULL UNIQUE,
    event_name VARCHAR(100) NOT NULL,
    PRIMARY KEY (signature_hash)
);

CREATE INDEX IF NOT EXISTS idx_event_signatures_event_name ON ethereum_event_signatures (event_name);
