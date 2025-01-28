-- Blocks table - Partitioned by network
CREATE TABLE IF NOT EXISTS blocks (
    chain VARCHAR(20) NOT NULL,
    block_number BIGINT NOT NULL,
    block_hash VARCHAR(128) NOT NULL,
    parent_hash VARCHAR(128),
    timestamp BIGINT NOT NULL,
    PRIMARY KEY (chain, block_hash)
) PARTITION BY LIST (chain);

-- Create partitions for each network
CREATE TABLE IF NOT EXISTS blocks_ethereum PARTITION OF blocks FOR VALUES IN ('ethereum');
CREATE TABLE IF NOT EXISTS blocks_bitcoin PARTITION OF blocks FOR VALUES IN ('bitcoin');
CREATE TABLE IF NOT EXISTS blocks_xrp PARTITION OF blocks FOR VALUES IN ('xrp');
CREATE TABLE IF NOT EXISTS blocks_solana PARTITION OF blocks FOR VALUES IN ('solana');
CREATE TABLE IF NOT EXISTS blocks_bnb PARTITION OF blocks FOR VALUES IN ('bnb');
CREATE TABLE IF NOT EXISTS blocks_base PARTITION OF blocks FOR VALUES IN ('base');
CREATE TABLE IF NOT EXISTS blocks_arbitrum PARTITION OF blocks FOR VALUES IN ('arbitrum');

-- Block-specific indexes
CREATE INDEX IF NOT EXISTS idx_blocks_timestamp 
    ON blocks USING brin (timestamp) WITH (pages_per_range = 128);
CREATE INDEX IF NOT EXISTS idx_blocks_hash 
    ON blocks USING btree (block_hash, chain);

-- EVM Transactions - Partitioned by network
CREATE TABLE IF NOT EXISTS base_evm_transactions (
    block_number BIGINT NOT NULL,
    network VARCHAR(20) NOT NULL,
    transaction_hash VARCHAR(128) NOT NULL,
    chain_id BIGINT NOT NULL,
    from_address VARCHAR(64) NOT NULL,
    to_address VARCHAR(64),
    value_wei NUMERIC(78, 0) NOT NULL,
    total_gas BIGINT NOT NULL,
    timestamp BIGINT NOT NULL,
    CONSTRAINT pk_evm_transactions PRIMARY KEY (network, timestamp, transaction_hash)
) PARTITION BY LIST (network);

-- Create network partitions
CREATE TABLE IF NOT EXISTS base_evm_transactions_ethereum PARTITION OF base_evm_transactions FOR VALUES IN ('ethereum');
CREATE TABLE IF NOT EXISTS base_evm_transactions_bnb PARTITION OF base_evm_transactions FOR VALUES IN ('bnb');
CREATE TABLE IF NOT EXISTS base_evm_transactions_base PARTITION OF base_evm_transactions FOR VALUES IN ('base');
CREATE TABLE IF NOT EXISTS base_evm_transactions_arbitrum PARTITION OF base_evm_transactions FOR VALUES IN ('arbitrum');

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
    full_signature VARCHAR(128) NOT NULL,
    input_types TEXT NOT NULL,
    indexed_inputs TEXT NOT NULL,
    inputs TEXT NOT NULL,
    contract_address VARCHAR(64) NOT NULL,
    factory_address VARCHAR(64),
    CONSTRAINT pk_evm_events PRIMARY KEY (network, signature_hash)
) PARTITION BY LIST (network);

-- Create partitions for each network
CREATE TABLE IF NOT EXISTS evm_known_events_ethereum PARTITION OF evm_known_events FOR VALUES IN ('ethereum');
CREATE TABLE IF NOT EXISTS evm_known_events_bnb PARTITION OF evm_known_events FOR VALUES IN ('bnb');
CREATE TABLE IF NOT EXISTS evm_known_events_base PARTITION OF evm_known_events FOR VALUES IN ('base');
CREATE TABLE IF NOT EXISTS evm_known_events_arbitrum PARTITION OF evm_known_events FOR VALUES IN ('arbitrum');


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
CREATE TABLE IF NOT EXISTS evm_contract_abis_ethereum PARTITION OF evm_contract_abis FOR VALUES IN ('ethereum');
CREATE TABLE IF NOT EXISTS evm_contract_abis_bnb PARTITION OF evm_contract_abis FOR VALUES IN ('bnb');
CREATE TABLE IF NOT EXISTS evm_contract_abis_base PARTITION OF evm_contract_abis FOR VALUES IN ('base');
CREATE TABLE IF NOT EXISTS evm_contract_abis_arbitrum PARTITION OF evm_contract_abis FOR VALUES IN ('arbitrum');

CREATE INDEX IF NOT EXISTS idx_evm_contract_abis_address ON evm_contract_abis
    USING btree (network, contract_address);

-- EVM Contract Info table
CREATE TABLE IF NOT EXISTS evm_swap (
    contract_address VARCHAR(64) NOT NULL,
    factory_address VARCHAR(64) NOT NULL,
    fee INT,
    token0_name VARCHAR(100),
    token1_name VARCHAR(100),
    token0_address VARCHAR(64),
    token1_address VARCHAR(64),
    name VARCHAR(100),
    network VARCHAR(20) NOT NULL,
    CONSTRAINT pk_evm_contract_info PRIMARY KEY (contract_address, network)
) PARTITION BY LIST (network);

CREATE TABLE IF NOT EXISTS evm_swap_ethereum PARTITION OF evm_swap FOR VALUES IN ('ethereum');
CREATE TABLE IF NOT EXISTS evm_swap_bnb PARTITION OF evm_swap FOR VALUES IN ('bnb');
CREATE TABLE IF NOT EXISTS evm_swap_base PARTITION OF evm_swap FOR VALUES IN ('base');
CREATE TABLE IF NOT EXISTS evm_swap_arbitrum PARTITION OF evm_swap FOR VALUES IN ('arbitrum');

CREATE INDEX IF NOT EXISTS idx_evm_swap_factory_address ON evm_swap
    USING btree (factory_address, network, contract_address, token0_address, token1_address);


-- EVM Token Info table

CREATE TABLE IF NOT EXISTS evm_token_info (
    contract_address VARCHAR(64) NOT NULL,
    name VARCHAR(100),
    symbol VARCHAR(100),
    network VARCHAR(20) NOT NULL,
    decimals INT,
    CONSTRAINT pk_evm_token_info PRIMARY KEY (contract_address, network)
) PARTITION BY LIST (network);

CREATE TABLE IF NOT EXISTS evm_token_info_ethereum PARTITION OF evm_token_info FOR VALUES IN ('ethereum');
CREATE TABLE IF NOT EXISTS evm_token_info_bnb PARTITION OF evm_token_info FOR VALUES IN ('bnb');
CREATE TABLE IF NOT EXISTS evm_token_info_base PARTITION OF evm_token_info FOR VALUES IN ('base');
CREATE TABLE IF NOT EXISTS evm_token_info_arbitrum PARTITION OF evm_token_info FOR VALUES IN ('arbitrum');

CREATE INDEX IF NOT EXISTS idx_evm_token_info_address ON evm_token_info
    USING btree (contract_address, network, name, symbol);


-- Change creator to factory
CREATE TABLE IF NOT EXISTS evm_contract_to_creator (
    contract_address VARCHAR(64) NOT NULL,
    factory_address VARCHAR(64) NOT NULL,
    network VARCHAR(20) NOT NULL,
    CONSTRAINT pk_evm_contract_to_creator PRIMARY KEY (contract_address, network)
) PARTITION BY LIST (network);

CREATE TABLE IF NOT EXISTS evm_contract_to_creator_ethereum PARTITION OF evm_contract_to_creator FOR VALUES IN ('ethereum');
CREATE TABLE IF NOT EXISTS evm_contract_to_creator_bnb PARTITION OF evm_contract_to_creator FOR VALUES IN ('bnb');
CREATE TABLE IF NOT EXISTS evm_contract_to_creator_base PARTITION OF evm_contract_to_creator FOR VALUES IN ('base');
CREATE TABLE IF NOT EXISTS evm_contract_to_creator_arbitrum PARTITION OF evm_contract_to_creator FOR VALUES IN ('arbitrum');

CREATE INDEX IF NOT EXISTS idx_evm_contract_to_creator_contract_address ON evm_contract_to_creator
    USING btree (factory_address, network);

CREATE TABLE IF NOT EXISTS evm_transaction_swap (
    network VARCHAR(20) NOT NULL,
    contract_address VARCHAR(64) NOT NULL,
    tx_hash VARCHAR(128) NOT NULL,
    log_index INT NOT NULL,
    timestamp BIGINT NOT NULL,
    amount0 NUMERIC(78, 0) NOT NULL,
    amount1 NUMERIC(78, 0) NOT NULL,
    token0 VARCHAR(100) NOT NULL,
    token1 VARCHAR(100) NOT NULL,
    amount0_in BOOLEAN NOT NULL,
    CONSTRAINT pk_evm_transaction_swap PRIMARY KEY (network, tx_hash, log_index)
) PARTITION BY LIST (network);

CREATE TABLE IF NOT EXISTS evm_transaction_swap_ethereum PARTITION OF evm_transaction_swap FOR VALUES IN ('ethereum');
CREATE TABLE IF NOT EXISTS evm_transaction_swap_bnb PARTITION OF evm_transaction_swap FOR VALUES IN ('bnb');
CREATE TABLE IF NOT EXISTS evm_transaction_swap_base PARTITION OF evm_transaction_swap FOR VALUES IN ('base');
CREATE TABLE IF NOT EXISTS evm_transaction_swap_arbitrum PARTITION OF evm_transaction_swap FOR VALUES IN ('arbitrum');

CREATE INDEX IF NOT EXISTS idx_evm_transaction_swap_tx_hash ON evm_transaction_swap
    USING btree (tx_hash, network, token0, token1, contract_address);

CREATE INDEX IF NOT EXISTS idx_evm_transaction_swap_timestamp 
    ON evm_transaction_swap USING brin (timestamp) WITH (pages_per_range = 128);





