// Create constraints for unique identifiers
CREATE CONSTRAINT tx_hash_unique IF NOT EXISTS
FOR (tx:Transaction) REQUIRE tx.txid IS UNIQUE;

CREATE CONSTRAINT address_unique IF NOT EXISTS
FOR (addr:Address) REQUIRE addr.address IS UNIQUE;

// Create indexes for common query patterns
CREATE INDEX tx_block_idx IF NOT EXISTS
FOR (tx:Transaction) ON (tx.block_height);

CREATE INDEX output_idx IF NOT EXISTS
FOR (out:Output) ON (out.value);

// Node structure
// Transaction nodes - stores minimal transaction data
CREATE (tx:Transaction {
    txid: $txid,                // Primary identifier
    block_height: $height,      // Block height for ordering
    is_coinbase: $is_coinbase   // Boolean flag for coinbase tx
});

// Output nodes - represents vout entries
CREATE (out:Output {
    tx_index: $n,              // The 'n' value from vout
    value: $value,             // BTC value
    spent: false               // Track if output is spent
});

// Address nodes - represents Bitcoin addresses
CREATE (addr:Address {
    address: $address          // The Bitcoin address
});

// Relationships
// SPENDS: Transaction -> Previous Output (for vin)
CREATE (tx:Transaction)-[:SPENDS]->(prev_out:Output);

// CREATES: Transaction -> Output (for vout)
CREATE (tx:Transaction)-[:CREATES]->(out:Output);

// CONTROLS: Address -> Output (ownership)
CREATE (addr:Address)-[:CONTROLS]->(out:Output);

// Example queries for common operations
// Find all outputs controlled by an address
MATCH (addr:Address {address: $address})-[:CONTROLS]->(out:Output)
WHERE out.spent = false
RETURN out;

// Trace transaction path
MATCH path = (tx1:Transaction)-[:CREATES]->(:Output)<-[:SPENDS]-(tx2:Transaction)
WHERE tx1.txid = $start_txid
RETURN path;

// Find total value received by address
MATCH (addr:Address {address: $address})-[:CONTROLS]->(out:Output)
WHERE out.spent = false
RETURN sum(out.value) as balance;