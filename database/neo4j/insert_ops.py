from .base import Neo4jDB
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from typing import List, Dict
import math

class Neo4jInsertOps:
    """
    Neo4j Insert Operations with optimized bulk processing and parallelization
    """
    def __init__(self, db: Neo4jDB, batch_size=500, max_workers=3):
        self.db = db
        self.batch_size = batch_size
        self.max_workers = max_workers

    def prepare_batch_data(self, batch: List[Dict]) -> Dict:
        """Prepare a batch of transactions for insertion."""
        batch_data = {
            'transactions': [],
            'outputs': [],
            'inputs': []
        }

        for txn in batch:
            # Prepare transaction data
            tx_data = {
                'txid': txn['txid'],
                'block_height': txn.get('block_height', 0),
                'is_coinbase': 'coinbase' in txn['vin'][0]
            }
            batch_data['transactions'].append(tx_data)

            # Prepare outputs data
            for vout in txn['vout']:
                if 'address' in vout['scriptPubKey']:
                    batch_data['outputs'].append({
                        'txid': txn['txid'],
                        'tx_index': vout['n'],
                        'value': vout['value'],
                        'address': vout['scriptPubKey']['address']
                    })

            # Prepare inputs data
            if not tx_data['is_coinbase']:
                for vin in txn['vin']:
                    batch_data['inputs'].append({
                        'current_txid': txn['txid'],
                        'prev_txid': vin['txid'],
                        'vout_index': vin['vout']
                    })

        return batch_data

    def process_batch(self, batch: List[Dict]) -> Dict:
        """Process a single batch of transactions."""
        stats = {
            'new_transactions': 0,
            'updated_transactions': 0,
            'new_addresses': 0,
            'new_outputs': 0
        }

        try:
            with self.db.driver.session() as session:
                def _batch_transaction_work(tx, batch_data):
                    # Batch create all transactions
                    tx_batch_query = """
                    UNWIND $txs as txn
                    MERGE (tx:Transaction {txid: txn.txid})
                    ON CREATE SET 
                        tx.block_height = txn.block_height,
                        tx.is_coinbase = txn.is_coinbase,
                        tx.created_at = timestamp()
                    ON MATCH SET 
                        tx.block_height = txn.block_height,
                        tx.is_coinbase = txn.is_coinbase,
                        tx.updated_at = timestamp()
                    WITH tx, CASE WHEN tx.created_at = timestamp() THEN true ELSE false END as was_created
                    RETURN count(tx) as tx_count, sum(CASE WHEN was_created THEN 1 ELSE 0 END) as new_count
                    """
                    
                    # Batch create addresses and outputs
                    output_batch_query = """
                    UNWIND $outputs as output
                    MATCH (tx:Transaction {txid: output.txid})
                    MERGE (addr:Address {address: output.address})
                    ON CREATE SET 
                        addr.created_at = timestamp()
                    WITH tx, addr, output, CASE WHEN addr.created_at = timestamp() THEN true ELSE false END as new_addr
                    CREATE (out:Output {
                        tx_index: output.tx_index,
                        value: output.value,
                        spent: false,
                        created_at: timestamp()
                    })
                    CREATE (tx)-[:CREATES]->(out)
                    CREATE (addr)-[:CONTROLS]->(out)
                    RETURN count(out) as output_count, sum(CASE WHEN new_addr THEN 1 ELSE 0 END) as new_addr_count
                    """

                    # Batch create input relationships
                    inputs_batch_query = """
                    UNWIND $inputs as input
                    MATCH (current_tx:Transaction {txid: input.current_txid})
                    MATCH (prev_tx:Transaction {txid: input.prev_txid})
                        -[:CREATES]->(prev_out:Output {tx_index: input.vout_index})
                    WHERE NOT prev_out.spent
                    SET prev_out.spent = true
                    CREATE (current_tx)-[:SPENDS]->(prev_out)
                    """

                    batch_data = self.prepare_batch_data(batch)
                    
                    # Execute transaction batch
                    tx_result = tx.run(tx_batch_query, {'txs': batch_data['transactions']})
                    tx_stats = tx_result.single()
                    stats['new_transactions'] = tx_stats['new_count']
                    stats['updated_transactions'] = tx_stats['tx_count'] - tx_stats['new_count']

                    # Execute outputs batch if exists
                    if batch_data['outputs']:
                        out_result = tx.run(output_batch_query, {'outputs': batch_data['outputs']})
                        out_stats = out_result.single()
                        stats['new_outputs'] = out_stats['output_count']
                        stats['new_addresses'] = out_stats['new_addr_count']

                    # Execute inputs batch if exists
                    if batch_data['inputs']:
                        tx.run(inputs_batch_query, {'inputs': batch_data['inputs']})

                    return stats

                return session.execute_write(_batch_transaction_work, batch)

        except Exception as e:
            self.db.logger.error(f"Error processing batch: {e}")
            raise

    def bulk_insert_transactions(self, transactions: List[Dict], parallel: bool = True) -> Dict:
        """
        Bulk insert transactions with optional parallelization.
        
        Args:
            transactions: List of transaction dictionaries
            parallel: Whether to use parallel processing (default: True)
        """
        start_time = time.time()
        total_stats = {
            'new_transactions': 0,
            'updated_transactions': 0,
            'new_addresses': 0,
            'new_outputs': 0
        }

        # Calculate optimal batch size and number of batches
        num_transactions = len(transactions)
        num_batches = math.ceil(num_transactions / self.batch_size)
        self.db.logger.info(f"Processing {num_transactions} transactions in {num_batches} batches")

        try:
            if parallel and num_batches > 1:
                # Parallel processing for multiple batches
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = []
                    
                    for i in range(0, num_transactions, self.batch_size):
                        batch = transactions[i:i + self.batch_size]
                        futures.append(executor.submit(self.process_batch, batch))

                    # Collect results and aggregate stats
                    for idx, future in enumerate(as_completed(futures), 1):
                        batch_stats = future.result()
                        for key in total_stats:
                            total_stats[key] += batch_stats[key]
                        self.db.logger.info(f"Completed batch {idx}/{num_batches}")
            else:
                # Sequential processing
                for i in range(0, num_transactions, self.batch_size):
                    batch = transactions[i:i + self.batch_size]
                    batch_stats = self.process_batch(batch)
                    for key in total_stats:
                        total_stats[key] += batch_stats[key]
                    self.db.logger.info(f"Completed batch {i//self.batch_size + 1}/{num_batches}")

        except Exception as e:
            self.db.logger.error(f"Error in bulk insert: {e}")
            raise

        duration = time.time() - start_time
        self.db.logger.info(
            f"Bulk insert complete. Processed {num_transactions} transactions "
            f"in {duration:.2f} seconds ({num_transactions/duration:.2f} tx/s). "
            f"Stats: {total_stats}"
        )
        return total_stats

    def insert_transaction(self, transaction: Dict) -> Dict:
        """Single transaction insert - uses bulk insert with a batch size of 1"""
        return self.bulk_insert_transactions([transaction], parallel=False)