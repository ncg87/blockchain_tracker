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

-- Index for parent-child lookups
CREATE INDEX IF NOT EXISTS idx_parent_child_hash ON blocks (parent_hash, block_hash);

-- Index for network and timestamp queries
CREATE INDEX IF NOT EXISTS idx_network_timestamp ON blocks (network, timestamp);

