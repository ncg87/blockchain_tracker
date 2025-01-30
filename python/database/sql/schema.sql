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
CREATE TABLE IF NOT EXISTS evm_transactions (
    block_number BIGINT NOT NULL,
    chain VARCHAR(20) NOT NULL,
    transaction_hash VARCHAR(128) NOT NULL,
    chain_id BIGINT NOT NULL,
    from_address VARCHAR(64) NOT NULL,
    to_address VARCHAR(64),
    amount NUMERIC(78, 0) NOT NULL,
    total_gas BIGINT NOT NULL,
    timestamp BIGINT NOT NULL,
    PRIMARY KEY (chain, timestamp, transaction_hash)
) PARTITION BY LIST (chain);

-- Create network partitions
CREATE TABLE IF NOT EXISTS evm_transactions_ethereum PARTITION OF evm_transactions FOR VALUES IN ('ethereum');
CREATE TABLE IF NOT EXISTS evm_transactions_bnb PARTITION OF evm_transactions FOR VALUES IN ('bnb');
CREATE TABLE IF NOT EXISTS evm_transactions_base PARTITION OF evm_transactions FOR VALUES IN ('base');
CREATE TABLE IF NOT EXISTS evm_transactions_arbitrum PARTITION OF evm_transactions FOR VALUES IN ('arbitrum');

-- EVM transaction indexes
CREATE INDEX IF NOT EXISTS idx_evm_tx_timestamp 
    ON evm_transactions USING brin (timestamp) WITH (pages_per_range = 128);
CREATE INDEX IF NOT EXISTS idx_evm_tx_from 
    ON evm_transactions USING btree (from_address, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_evm_tx_to 
    ON evm_transactions USING btree (to_address, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_evm_tx_hash 
    ON evm_transactions USING btree (transaction_hash);
CREATE INDEX IF NOT EXISTS idx_evm_tx_chain 
    ON evm_transactions USING btree (chain, timestamp DESC);


-- Bitcoin Transactions
CREATE TABLE IF NOT EXISTS bitcoin_transactions (
    block_number BIGINT NOT NULL,
    transaction_hash VARCHAR(128) NOT NULL,
    version SMALLINT NOT NULL,
    amount NUMERIC(20, 0) NOT NULL,
    timestamp BIGINT NOT NULL,
    fee NUMERIC(16, 8) NOT NULL,
    CONSTRAINT pk_bitcoin_transactions PRIMARY KEY (timestamp, transaction_hash)
);

-- Bitcoin transaction indexes
CREATE INDEX IF NOT EXISTS idx_bitcoin_tx_timestamp 
    ON bitcoin_transactions USING brin (timestamp) WITH (pages_per_range = 128);
CREATE INDEX IF NOT EXISTS idx_bitcoin_tx_hash 
    ON bitcoin_transactions USING btree (transaction_hash);
CREATE INDEX IF NOT EXISTS idx_bitcoin_tx_block 
    ON bitcoin_transactions USING btree (block_number);


-- XRP Transactions
CREATE TABLE IF NOT EXISTS xrp_transactions (
    block_number BIGINT NOT NULL,
    transaction_hash VARCHAR(128) NOT NULL,
    account VARCHAR(64) NOT NULL,
    type VARCHAR(20) NOT NULL,
    fee BIGINT NOT NULL,
    timestamp BIGINT NOT NULL,
    PRIMARY KEY (timestamp, transaction_hash)
);

-- XRP transaction indexes
CREATE INDEX IF NOT EXISTS idx_xrp_tx_timestamp 
    ON xrp_transactions USING brin (timestamp) WITH (pages_per_range = 128);
CREATE INDEX IF NOT EXISTS idx_xrp_tx_hash 
    ON xrp_transactions USING btree (transaction_hash);
CREATE INDEX IF NOT EXISTS idx_xrp_tx_account 
    ON xrp_transactions USING btree (account, timestamp DESC);

DROP TABLE IF EXISTS base_solana_transactions;

-- Solana Transactions
CREATE TABLE IF NOT EXISTS solana_transactions (
    block_number BIGINT NOT NULL,
    signature VARCHAR(128) NOT NULL,
    amount BIGINT NOT NULL,
    fee BIGINT NOT NULL,
    account_key VARCHAR(64) NOT NULL,
    timestamp BIGINT NOT NULL,
    PRIMARY KEY (timestamp, signature)
);
CREATE INDEX IF NOT EXISTS idx_solana_tx_timestamp 
    ON solana_transactions USING brin (timestamp) WITH (pages_per_range = 128);
-- Is this needed?
CREATE INDEX IF NOT EXISTS idx_solana_tx_signature 
    ON solana_transactions USING btree (signature);

CREATE INDEX IF NOT EXISTS idx_solana_tx_account 
    ON solana_transactions USING btree (account_key, timestamp DESC);

-- EVM Decoded Events -- Holds the decoded events, based on the signature hash for each chain, helps to determine non-native actions
CREATE TABLE IF NOT EXISTS evm_decoded_events (
    chain VARCHAR(20) NOT NULL,
    signature_hash VARCHAR(128) NOT NULL,
    event_name TEXT NOT NULL,
    decoded_signature TEXT NOT NULL,
    input_types TEXT NOT NULL,
    indexed_inputs TEXT NOT NULL,
    input_names TEXT NOT NULL,
    inputs TEXT NOT NULL,
    PRIMARY KEY (chain, signature_hash)
) PARTITION BY LIST (chain);

-- EVM Partitions
CREATE TABLE IF NOT EXISTS evm_decoded_events_ethereum PARTITION OF evm_decoded_events FOR VALUES IN ('ethereum');
CREATE TABLE IF NOT EXISTS evm_decoded_events_bnb PARTITION OF evm_decoded_events FOR VALUES IN ('bnb');
CREATE TABLE IF NOT EXISTS evm_decoded_events_base PARTITION OF evm_decoded_events FOR VALUES IN ('base');
CREATE TABLE IF NOT EXISTS evm_decoded_events_arbitrum PARTITION OF evm_decoded_events FOR VALUES IN ('arbitrum');

CREATE INDEX IF NOT EXISTS idx_evm_events_signature 
    ON evm_decoded_events USING btree (signature_hash);

-- Create new partitioned contract ABIs table
CREATE TABLE IF NOT EXISTS evm_contract_abis (
    chain VARCHAR(20) NOT NULL,
    contract_address VARCHAR(64) NOT NULL,
    abi TEXT NOT NULL,
    CONSTRAINT pk_evm_contract_abis PRIMARY KEY (chain, contract_address)
) PARTITION BY LIST (chain);

-- EVM Partitions
CREATE TABLE IF NOT EXISTS evm_contract_abis_ethereum PARTITION OF evm_contract_abis FOR VALUES IN ('ethereum');
CREATE TABLE IF NOT EXISTS evm_contract_abis_bnb PARTITION OF evm_contract_abis FOR VALUES IN ('bnb');
CREATE TABLE IF NOT EXISTS evm_contract_abis_base PARTITION OF evm_contract_abis FOR VALUES IN ('base');
CREATE TABLE IF NOT EXISTS evm_contract_abis_arbitrum PARTITION OF evm_contract_abis FOR VALUES IN ('arbitrum');

-- EVM Contract ABIs Indexes
CREATE INDEX IF NOT EXISTS idx_evm_contract_abis_address 
    ON evm_contract_abis USING btree (contract_address, chain);

-- EVM Swap Info table

-- Adjust so that it can hold all the info about a token, contract, name, decimals, symbol, etc.
CREATE TABLE IF NOT EXISTS evm_swap_info (
    contract_address VARCHAR(64) NOT NULL,
    factory_address VARCHAR(64) NOT NULL,
    fee INT,
    token0_name VARCHAR(100),
    token1_name VARCHAR(100),
    token0_address VARCHAR(64),
    token1_address VARCHAR(64),
    name VARCHAR(100),
    chain VARCHAR(20) NOT NULL,
    PRIMARY KEY (contract_address, chain)
) PARTITION BY LIST (chain);

CREATE TABLE IF NOT EXISTS evm_swap_info_ethereum PARTITION OF evm_swap_info FOR VALUES IN ('ethereum');
CREATE TABLE IF NOT EXISTS evm_swap_info_bnb PARTITION OF evm_swap_info FOR VALUES IN ('bnb');
CREATE TABLE IF NOT EXISTS evm_swap_info_base PARTITION OF evm_swap_info FOR VALUES IN ('base');
CREATE TABLE IF NOT EXISTS evm_swap_info_arbitrum PARTITION OF evm_swap_info FOR VALUES IN ('arbitrum');

-- For when we want to get all the swap info of a contract
CREATE INDEX IF NOT EXISTS idx_evm_swap_contract 
    ON evm_swap_info USING btree (contract_address, chain);

-- For when we want to get all the swaps for a factory
CREATE INDEX IF NOT EXISTS idx_evm_swap_factory 
    ON evm_swap_info USING btree (factory_address, chain);


-- EVM Token Info table

CREATE TABLE IF NOT EXISTS evm_token_info (
    contract_address VARCHAR(64) NOT NULL,
    name VARCHAR(100),
    symbol VARCHAR(100),
    decimals INT NOT NULL,
    chain VARCHAR(20) NOT NULL,
    CONSTRAINT pk_evm_token_info PRIMARY KEY (contract_address, chain)
) PARTITION BY LIST (chain);

CREATE TABLE IF NOT EXISTS evm_token_info_ethereum PARTITION OF evm_token_info FOR VALUES IN ('ethereum');
CREATE TABLE IF NOT EXISTS evm_token_info_bnb PARTITION OF evm_token_info FOR VALUES IN ('bnb');
CREATE TABLE IF NOT EXISTS evm_token_info_base PARTITION OF evm_token_info FOR VALUES IN ('base');
CREATE TABLE IF NOT EXISTS evm_token_info_arbitrum PARTITION OF evm_token_info FOR VALUES IN ('arbitrum');

CREATE INDEX IF NOT EXISTS idx_evm_token_info_address ON evm_token_info
    USING btree (contract_address, chain);

-- Change creator to factory
CREATE TABLE IF NOT EXISTS evm_contract_to_factory (
    contract_address VARCHAR(64) NOT NULL,
    factory_address VARCHAR(64) NOT NULL,
    chain VARCHAR(20) NOT NULL,
    name VARCHAR(100),
    CONSTRAINT pk_evm_contract_to_factory PRIMARY KEY (contract_address, chain)
) PARTITION BY LIST (chain);

-- Factory Partitions
CREATE TABLE IF NOT EXISTS evm_contract_to_factory_ethereum PARTITION OF evm_contract_to_factory FOR VALUES IN ('ethereum');
CREATE TABLE IF NOT EXISTS evm_contract_to_factory_bnb PARTITION OF evm_contract_to_factory FOR VALUES IN ('bnb');
CREATE TABLE IF NOT EXISTS evm_contract_to_factory_base PARTITION OF evm_contract_to_factory FOR VALUES IN ('base');
CREATE TABLE IF NOT EXISTS evm_contract_to_factory_arbitrum PARTITION OF evm_contract_to_factory FOR VALUES IN ('arbitrum');

-- Factory Indexes
CREATE INDEX IF NOT EXISTS idx_evm_contract_to_factory_contract 
    ON evm_contract_to_factory USING btree (contract_address, chain);
CREATE INDEX IF NOT EXISTS idx_evm_contract_to_factory_factory 
    ON evm_contract_to_factory USING btree (factory_address, chain);

-- Adjust so that it can hold all the info about a token, contract, name, decimals, symbol, etc.
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





