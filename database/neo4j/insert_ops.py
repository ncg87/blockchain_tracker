from .base import Neo4jDB

class Neo4jInsertOps:
    """
    Neo4j Insert Operations
    """
    def __init__(self, db: Neo4jDB):
        self.db = db

    def insert_transaction(self, transaction):
        """Insert a Bitcoin transaction and its relationships into Neo4j."""
        self.db.logger.info(f"Inserting transaction {transaction['txid']} into Neo4j database")
        
        stats = {
            'new_transactions': 0,
            'updated_transactions': 0,
            'new_addresses': 0,
            'new_outputs': 0
        }
        
        try:
            with self.db.driver.session() as session:
                def _transaction_work(tx):
                    # Handle transaction creation
                    tx_params = {
                        'txid': transaction['txid'],
                        'block_height': transaction.get('block_height', 0),
                        'is_coinbase': 'coinbase' in transaction['vin'][0]
                    }
                    
                    create_tx_query = """
                    MERGE (tx:Transaction {txid: $txid})
                    ON CREATE SET 
                        tx.block_height = $block_height,
                        tx.is_coinbase = $is_coinbase,
                        tx.created_at = timestamp()
                    ON MATCH SET 
                        tx.block_height = $block_height,
                        tx.is_coinbase = $is_coinbase,
                        tx.updated_at = timestamp()
                    WITH tx, CASE WHEN tx.created_at = timestamp() THEN true ELSE false END as was_created
                    RETURN tx, was_created
                    """
                    result = tx.run(create_tx_query, tx_params)
                    tx_record = result.single()
                    if tx_record and tx_record['was_created']:
                        stats['new_transactions'] += 1
                        self.db.logger.info(f"Created new transaction node for {transaction['txid']}")
                    else:
                        stats['updated_transactions'] += 1
                        self.db.logger.info(f"Updated existing transaction node for {transaction['txid']}")

                    # Handle outputs (vout)
                    for vout in transaction['vout']:
                        if 'address' in vout['scriptPubKey']:
                            output_params = {
                                'txid': transaction['txid'],
                                'tx_index': vout['n'],
                                'value': vout['value'],
                                'address': vout['scriptPubKey']['address']
                            }
                            
                            create_output_query = """
                            MATCH (tx:Transaction {txid: $txid})
                            MERGE (addr:Address {address: $address})
                            ON CREATE SET addr.created_at = timestamp()
                            WITH tx, addr
                            CREATE (out:Output {
                                tx_index: $tx_index,
                                value: $value,
                                spent: false,
                                created_at: timestamp()
                            })
                            CREATE (tx)-[:CREATES]->(out)
                            CREATE (addr)-[:CONTROLS]->(out)
                            RETURN out.created_at as output_created, addr.created_at as addr_created
                            """
                            output_result = tx.run(create_output_query, output_params)
                            out_record = output_result.single()
                            if out_record:
                                if out_record['addr_created']:
                                    stats['new_addresses'] += 1
                                    self.db.logger.info(f"Created new address node for {output_params['address']}")
                                stats['new_outputs'] += 1
                                self.db.logger.info(f"Created new output node for tx {transaction['txid']} index {vout['n']}")

                    # Handle inputs (vin)
                    if not tx_params['is_coinbase']:
                        for vin in transaction['vin']:
                            input_params = {
                                'current_txid': transaction['txid'],
                                'prev_txid': vin['txid'],
                                'vout_index': vin['vout']
                            }
                            
                            create_input_query = """
                            MATCH (current_tx:Transaction {txid: $current_txid})
                            MATCH (prev_tx:Transaction {txid: $prev_txid})
                            -[:CREATES]->(prev_out:Output {tx_index: $vout_index})
                            SET prev_out.spent = true
                            CREATE (current_tx)-[:SPENDS]->(prev_out)
                            """
                            tx.run(create_input_query, input_params)

                # Execute all operations in a single transaction
                session.execute_write(_transaction_work)
                
                return stats

        except Exception as e:
            self.db.logger.error(f"Error inserting transaction: {e}")
            raise

    def bulk_insert_transactions(self, transactions):
        """Bulk insert multiple transactions."""
        stats = {
            'new_transactions': 0,
            'updated_transactions': 0,
            'new_addresses': 0,
            'new_outputs': 0
        }
        
        for tx in transactions:
            # Update your insert_transaction to return stats
            tx_stats = self.insert_transaction(tx)
            for key in stats:
                stats[key] += tx_stats.get(key, 0)
        
        self.db.logger.info(f"Bulk insert complete. Stats: {stats}")
        return stats