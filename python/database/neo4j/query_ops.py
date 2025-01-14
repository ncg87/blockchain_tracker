from .base import Neo4jDB
from typing import List, Dict, Optional

class Neo4jQueryOps:
    def __init__(self, db: Neo4jDB):
        self.db = db
    
    def get_transaction(self, txid: str) -> Optional[Dict]:
        """Get transaction details including inputs and outputs."""
        self.db.logger.info(f"Getting transaction {txid} from Neo4j database")
        
        query = """
        MATCH (tx:Transaction {txid: $txid})
        OPTIONAL MATCH (tx)-[:CREATES]->(out:Output)<-[:CONTROLS]-(addr:Address)
        OPTIONAL MATCH (tx)-[:SPENDS]->(prev_out:Output)<-[:CREATES]-(prev_tx:Transaction)
        RETURN tx, collect(DISTINCT {
            index: out.tx_index,
            value: out.value,
            address: addr.address,
            spent: out.spent
        }) as outputs,
        collect(DISTINCT {
            txid: prev_tx.txid,
            index: prev_out.tx_index,
            value: prev_out.value
        }) as inputs
        """
        
        with self.db.driver.session() as session:
            result = session.run(query, {'txid': txid}).single()
            return result if result else None

    def get_address_balance(self, address: str) -> float:
        """Get current balance for an address."""
        query = """
        MATCH (addr:Address {address: $address})-[:CONTROLS]->(out:Output)
        WHERE out.spent = false
        RETURN sum(out.value) as balance
        """
        
        with self.db.driver.session() as session:
            result = session.run(query, {'address': address}).single()
            return result['balance'] if result and result['balance'] else 0.0

    def trace_transaction_flow(self, start_txid: str, depth: int = 3) -> List[Dict]:
        """Trace transaction flow up to specified depth."""
        query = """
        MATCH path = (start_tx:Transaction {txid: $txid})
        -[:CREATES|SPENDS*..%d]->(tx:Transaction)
        RETURN path
        """ % depth
        
        with self.db.driver.session() as session:
            return list(session.run(query, {'txid': start_txid}))

    def find_common_addresses(self, address1: str, address2: str) -> List[str]:
        """Find transactions involving both addresses."""
        query = """
        MATCH (addr1:Address {address: $addr1})-[:CONTROLS]->(:Output)<-[:CREATES]-(tx:Transaction)
        -[:CREATES]->(:Output)<-[:CONTROLS]-(addr2:Address {address: $addr2})
        RETURN DISTINCT tx.txid
        """
        
        with self.db.driver.session() as session:
            result = session.run(query, {'addr1': address1, 'addr2': address2})
            return [record['tx.txid'] for record in result]

    def get_address_transactions(self, address: str, limit: int = 100) -> List[Dict]:
        """Get all transactions involving an address."""
        query = """
        MATCH (addr:Address {address: $address})-[:CONTROLS]->(out:Output)<-[:CREATES]-(tx:Transaction)
        RETURN DISTINCT tx.txid, tx.block_height, out.value, out.spent
        ORDER BY tx.block_height DESC
        LIMIT $limit
        """
        
        with self.db.driver.session() as session:
            result = session.run(query, {'address': address, 'limit': limit})
            return [dict(record) for record in result]

    def find_address_clusters(self, min_cluster_size: int = 2) -> List[List[str]]:
        """Find clusters of addresses that frequently transact together."""
        query = """
        MATCH (addr1:Address)-[:CONTROLS]->(:Output)<-[:CREATES]-(tx:Transaction)
        -[:CREATES]->(:Output)<-[:CONTROLS]-(addr2:Address)
        WHERE addr1 <> addr2
        WITH addr1, addr2, count(tx) as num_transactions
        WHERE num_transactions >= $min_size
        RETURN collect(DISTINCT addr1.address) as cluster
        """
        
        with self.db.driver.session() as session:
            result = session.run(query, {'min_size': min_cluster_size})
            return [record['cluster'] for record in result]

    def get_transaction_volume(self, address: str, days: int = 30) -> float:
        """Get transaction volume for an address over specified days."""
        query = """
        MATCH (addr:Address {address: $address})-[:CONTROLS]->(out:Output)<-[:CREATES]-(tx:Transaction)
        WHERE tx.block_height >= $start_height
        RETURN sum(out.value) as volume
        """
        
        # Approximate blocks for days (144 blocks per day on average)
        blocks_ago = days * 144
        
        with self.db.driver.session() as session:
            result = session.run(query, {
                'address': address,
                'start_height': -blocks_ago  # Assumes negative height for recent blocks
            }).single()
            return result['volume'] if result and result['volume'] else 0.0