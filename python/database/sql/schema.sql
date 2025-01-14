-- Blocks table - Partitioned by network
CREATE TABLE IF NOT EXISTS blocks (
    id SERIAL,
    network VARCHAR(20) NOT NULL,
    block_number BIGINT NOT NULL,
    block_hash VARCHAR(128) NOT NULL,
    parent_hash VARCHAR(128),
    timestamp BIGINT NOT NULL,
    CONSTRAINT pk_blocks PRIMARY KEY (network, block_number, id),
    CONSTRAINT uq_blocks_hash UNIQUE (network, block_hash)  -- Added network to unique constraint
) PARTITION BY LIST (network);

-- Create partitions for each network
CREATE TABLE IF NOT EXISTS blocks_ethereum PARTITION OF blocks FOR VALUES IN ('Ethereum');
CREATE TABLE IF NOT EXISTS blocks_bitcoin PARTITION OF blocks FOR VALUES IN ('Bitcoin');
CREATE TABLE IF NOT EXISTS blocks_xrp PARTITION OF blocks FOR VALUES IN ('XRP');
CREATE TABLE IF NOT EXISTS blocks_solana PARTITION OF blocks FOR VALUES IN ('Solana');
CREATE TABLE IF NOT EXISTS blocks_bnb PARTITION OF blocks FOR VALUES IN ('BNB');
CREATE TABLE IF NOT EXISTS blocks_base PARTITION OF blocks FOR VALUES IN ('Base');

-- Block-specific indexes
CREATE INDEX IF NOT EXISTS idx_blocks_timestamp ON blocks USING brin (timestamp) WITH (pages_per_range = 128);

-- EVM Transactions - Partitioned by network
CREATE TABLE IF NOT EXISTS base_evm_transactions (
    block_number BIGINT NOT NULL,
    network VARCHAR(20) NOT NULL,
    transaction_hash VARCHAR(128) NOT NULL,
    chain_id SMALLINT NOT NULL,
    from_address VARCHAR(64) NOT NULL,
    to_address VARCHAR(64),
    value_wei NUMERIC(78, 0) NOT NULL,
    total_gas BIGINT NOT NULL,
    timestamp BIGINT NOT NULL,
    CONSTRAINT pk_evm_transactions PRIMARY KEY (network, timestamp, transaction_hash)
) PARTITION BY LIST (network);

-- Create network partitions
CREATE TABLE IF NOT EXISTS base_evm_transactions_ethereum PARTITION OF base_evm_transactions FOR VALUES IN ('Ethereum');
CREATE TABLE IF NOT EXISTS base_evm_transactions_bnb PARTITION OF base_evm_transactions FOR VALUES IN ('BNB');
CREATE TABLE IF NOT EXISTS base_evm_transactions_base PARTITION OF base_evm_transactions FOR VALUES IN ('Base');

-- EVM transaction indexes
CREATE INDEX IF NOT EXISTS idx_evm_tx_from ON base_evm_transactions 
    USING btree (from_address, timestamp DESC) 
    INCLUDE (network, block_number, value_wei);
CREATE INDEX IF NOT EXISTS idx_evm_tx_to ON base_evm_transactions 
    USING btree (to_address, timestamp DESC) 
    INCLUDE (network, block_number, value_wei);
CREATE INDEX IF NOT EXISTS idx_evm_tx_block ON base_evm_transactions 
    USING btree (network, block_number);

-- Bitcoin Transactions
CREATE TABLE IF NOT EXISTS base_bitcoin_transactions (
    block_number BIGINT NOT NULL,
    transaction_id VARCHAR(128) NOT NULL,
    version SMALLINT NOT NULL,
    value_satoshis NUMERIC(20, 0) NOT NULL,
    timestamp BIGINT NOT NULL,
    fee NUMERIC(16, 8) NOT NULL,
    CONSTRAINT pk_bitcoin_transactions PRIMARY KEY (timestamp, transaction_id)
);

-- Bitcoin transaction indexes
CREATE INDEX IF NOT EXISTS idx_bitcoin_tx_block ON base_bitcoin_transactions 
    USING btree (block_number) 
    INCLUDE (value_satoshis, fee);
CREATE INDEX IF NOT EXISTS idx_bitcoin_tx_timestamp ON base_bitcoin_transactions 
    USING btree (timestamp);

-- XRP Transactions
CREATE TABLE IF NOT EXISTS base_xrp_transactions (
    block_number BIGINT NOT NULL,
    transaction_hash VARCHAR(128) NOT NULL,
    account VARCHAR(64) NOT NULL,
    type VARCHAR(20) NOT NULL,
    fee BIGINT NOT NULL,
    timestamp BIGINT NOT NULL,
    CONSTRAINT pk_xrp_transactions PRIMARY KEY (timestamp, transaction_hash)
);

-- XRP transaction indexes
CREATE INDEX IF NOT EXISTS idx_xrp_tx_account ON base_xrp_transactions 
    USING btree (account, timestamp DESC) 
    INCLUDE (type, fee);
CREATE INDEX IF NOT EXISTS idx_xrp_tx_timestamp ON base_xrp_transactions 
    USING btree (timestamp);

-- Solana Transactions
CREATE TABLE IF NOT EXISTS base_solana_transactions (
    block_number BIGINT NOT NULL,
    signature VARCHAR(128) NOT NULL,
    value_lamports BIGINT NOT NULL,
    fee_lamports BIGINT NOT NULL,
    account_key VARCHAR(64) NOT NULL,
    timestamp BIGINT NOT NULL,
    CONSTRAINT pk_solana_transactions PRIMARY KEY (timestamp, signature)
);

-- Solana transaction indexes
CREATE INDEX IF NOT EXISTS idx_solana_tx_account ON base_solana_transactions 
    USING btree (account_key, timestamp DESC) 
    INCLUDE (value_lamports, fee_lamports);
CREATE INDEX IF NOT EXISTS idx_solana_tx_timestamp ON base_solana_transactions 
    USING btree (timestamp);


-- Ethereum Known Events table
CREATE TABLE IF NOT EXISTS ethereum_known_events (
    signature_hash VARCHAR(128) NOT NULL,
    name VARCHAR(100) NOT NULL,
    full_signature VARCHAR(100) NOT NULL,
    input_types VARCHAR(100) NOT NULL,
    indexed_inputs VARCHAR(100) NOT NULL,
    inputs TEXT NOT NULL,
    CONSTRAINT pk_signature_hash PRIMARY KEY (signature_hash)
) WITH (fillfactor = 100);
CREATE INDEX IF NOT EXISTS idx_signature_hash ON ethereum_known_events
    USING btree (signature_hash);


-- Ethereum Contract ABIs table
CREATE TABLE IF NOT EXISTS ethereum_contract_abis (
    contract_address VARCHAR(64) NOT NULL,
    abi TEXT NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_contract_address PRIMARY KEY (contract_address)
) WITH (fillfactor = 100);

CREATE INDEX IF NOT EXISTS idx_contract_address ON ethereum_contract_abis
    USING btree (contract_address);


-- Create the new partitioned tables
CREATE TABLE IF NOT EXISTS evm_known_events (
    network VARCHAR(20) NOT NULL,
    signature_hash VARCHAR(128) NOT NULL,
    name TEXT NOT NULL,
    full_signature VARCHAR(100) NOT NULL,
    input_types VARCHAR(100) NOT NULL,
    indexed_inputs VARCHAR(100) NOT NULL,
    inputs TEXT NOT NULL,
    CONSTRAINT pk_evm_events PRIMARY KEY (network, signature_hash)
) PARTITION BY LIST (network);

-- Create partitions for each network
CREATE TABLE IF NOT EXISTS evm_known_events_ethereum PARTITION OF evm_known_events FOR VALUES IN ('Ethereum');
CREATE TABLE IF NOT EXISTS evm_known_events_bnb PARTITION OF evm_known_events FOR VALUES IN ('BNB');
CREATE TABLE IF NOT EXISTS evm_known_events_base PARTITION OF evm_known_events FOR VALUES IN ('Base');

CREATE INDEX IF NOT EXISTS idx_evm_events_signature ON evm_known_events
    USING btree (network, signature_hash);

-- Create new partitioned contract ABIs table
CREATE TABLE IF NOT EXISTS evm_contract_abis (
    network VARCHAR(20) NOT NULL,
    contract_address VARCHAR(64) NOT NULL,
    abi TEXT NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_evm_contract_abis PRIMARY KEY (network, contract_address)
) PARTITION BY LIST (network);

-- Create partitions for each network
CREATE TABLE IF NOT EXISTS evm_contract_abis_ethereum PARTITION OF evm_contract_abis FOR VALUES IN ('Ethereum');
CREATE TABLE IF NOT EXISTS evm_contract_abis_bnb PARTITION OF evm_contract_abis FOR VALUES IN ('BNB');
CREATE TABLE IF NOT EXISTS evm_contract_abis_base PARTITION OF evm_contract_abis FOR VALUES IN ('Base');

-- Recreate indexes

CREATE INDEX IF NOT EXISTS idx_evm_contract_abis_address ON evm_contract_abis
    USING btree (network, contract_address);
