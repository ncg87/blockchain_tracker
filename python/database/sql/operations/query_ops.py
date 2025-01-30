from ..base import SQLDatabase
from datetime import datetime
from typing import List, Optional, Dict, Any
from psycopg2.extras import RealDictCursor
from .blocks import BlockQueryOperations
from .evm import EVMQueryOperations
from .bitcoin import BitcoinQueryOperations
from .solana import SolanaQueryOperations
from .xrp import XRPQueryOperations
from .api import APIQueryOperations

class SQLQueryOperations:
    """
    Query operations class optimized for PostgreSQL.
    """
    def __init__(self, db: SQLDatabase):
        self.db = db
        # Use RealDictCursor for more convenient dictionary access
        self.db.cursor = self.db.conn.cursor(cursor_factory=RealDictCursor)
        
        self.block = BlockQueryOperations(self.db)
        self.evm = EVMQueryOperations(self.db)
        self.bitcoin = BitcoinQueryOperations(self.db)
        self.solana = SolanaQueryOperations(self.db)
        self.xrp = XRPQueryOperations(self.db)
        self.api = APIQueryOperations(self.db)

    def query_blocks_by_time(self, start_time: int, end_time: int) -> List[Dict[str, Any]]:
        return self.block.query_by_time(start_time, end_time)
    
    def query_blocks(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.block.query_recent(limit)
    
    def query_blocks_by_network(self, network: str, block_number: Optional[int] = None) -> List[Dict[str, Any]]:
        return self.block.query_by_network(network, block_number)
    
    def query_recent_blocks_by_network(self, network: str, limit: int = 10) -> List[Dict[str, Any]]:
        return self.block.query_recent_by_network(network, limit)
       
    def query_evm_transactions(self, network: str, block_number: int) -> List[Dict[str, Any]]:
        return self.evm.query_transactions(network, block_number)

    def query_recent_evm_transactions(self, network: str, limit: int = 100) -> List[Dict[str, Any]]:
        return self.evm.query_recent_transactions(network, limit)

    def query_bitcoin_transactions(self, block_number: int) -> List[Dict[str, Any]]:
        return self.bitcoin.query_transactions(block_number)
    
    def query_recent_bitcoin_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.bitcoin.query_recent_transactions(limit)

    def query_solana_transactions(self, block_number: int) -> List[Dict[str, Any]]:
        return self.solana.query_transactions(block_number)
    
    def query_recent_solana_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.solana.query_recent_transactions(limit)
    
    def query_xrp_transactions(self, block_number: int) -> List[Dict[str, Any]]:
        return self.xrp.query_transactions(block_number)
    
    def query_recent_xrp_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.xrp.query_recent_transactions(limit)
    
    def query_evm_address_history(self, network: str, address: str, start_time: int, end_time: int) -> List[Dict[str, Any]]:
        return self.evm.query_address_history(network, address, start_time, end_time)

    def query_evm_event(self, network: str, signature_hash: str) -> Optional[Dict[str, Any]]:
        return self.evm.query_event(network, signature_hash)
        
    def query_evm_contract_abi(self, network: str, contract_address: str) -> Optional[Dict[str, Any]]:
        return self.evm.query_contract_abi(network, contract_address)
        
    def query_evm_swap(self, network: str, contract_address: str) -> Optional[Dict[str, Any]]:
        return self.evm.query_swap(network, contract_address)
    
    def query_high_value_transactions(self, network: str, min_value: int) -> List[Dict[str, Any]]:
        """
        Query high-value transactions using the partial index.
        """
        try:
            if network == 'bitcoin':
                self.db.cursor.execute("""
                    SELECT block_number, transaction_id, value_satoshis, timestamp, fee
                    FROM base_bitcoin_transactions
                    WHERE value_satoshis > %s
                    ORDER BY value_satoshis DESC
                    LIMIT 100
                """, (min_value,))
            elif network in ['ethereum', 'bsc']:
                self.db.cursor.execute("""
                    SELECT block_number, transaction_hash, from_address, to_address, 
                           value_wei, timestamp
                    FROM base_evm_transactions
                    WHERE network = %s AND value_wei > %s
                    ORDER BY value_wei DESC
                    LIMIT 100
                """, (network, min_value))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying high-value transactions: {e}")
            return []