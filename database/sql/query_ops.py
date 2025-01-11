from .base import SQLDatabase
from datetime import datetime
from typing import List, Optional, Dict, Any
from psycopg2.extras import RealDictCursor

class SQLQueryOperations:
    """
    Query operations class optimized for PostgreSQL.
    """
    def __init__(self, db: SQLDatabase):
        self.db = db
        # Use RealDictCursor for more convenient dictionary access
        self.db.cursor = self.db.conn.cursor(cursor_factory=RealDictCursor)

    def query_blocks_by_time(self, start_time: int, end_time: int) -> List[Dict[str, Any]]:
        """
        Query blocks within a specified time range.
        """
        try:
            self.db.logger.info(f"Querying blocks between {start_time} and {end_time}")

            query = """
                SELECT id, network, block_number, block_hash, parent_hash, timestamp 
                FROM blocks 
                WHERE timestamp BETWEEN %s AND %s
                ORDER BY timestamp ASC;
            """
            
            self.db.cursor.execute(query, (start_time, end_time))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying blocks by time: {e}")
            return []
    
    def query_blocks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Query recent blocks across all networks.
        """
        try:
            query = """
                SELECT id, network, block_number, block_hash, parent_hash, timestamp
                FROM blocks 
                ORDER BY block_number DESC 
                LIMIT %s;
            """
            
            self.db.cursor.execute(query, (limit,))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying blocks: {e}")
            return []
    
    def query_by_network(self, network: str, block_number: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Query block(s) for a specific network.
        """
        try:
            self.db.logger.info(f"Querying blocks for network {network} with block_number={block_number}")
            
            if block_number is not None:
                query = """
                    SELECT id, network, block_number, block_hash, parent_hash, timestamp
                    FROM blocks
                    WHERE network = %s AND block_number = %s;
                """
                self.db.cursor.execute(query, (network, block_number))
            else:
                query = """
                    SELECT id, network, block_number, block_hash, parent_hash, timestamp
                    FROM blocks
                    WHERE network = %s
                    ORDER BY block_number DESC
                    LIMIT 1000;
                """
                self.db.cursor.execute(query, (network,))
            
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying blocks for network {network}: {e}")
            return []
        
    def query_evm_transactions(self, network: str, block_number: int) -> List[Dict[str, Any]]:
        """
        Query EVM transactions for a specific block.
        """
        try:
            query = """
                SELECT block_number, network, transaction_hash, chain_id, 
                       from_address, to_address, value_wei, total_gas, timestamp
                FROM base_evm_transactions 
                WHERE network = %s AND block_number = %s;
            """
            
            self.db.cursor.execute(query, (network, block_number))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying transactions for network {network}: {e}")
            return []

    def query_bitcoin_transactions(self, block_number: int) -> List[Dict[str, Any]]:
        """
        Query Bitcoin transactions for a specific block.
        """
        try:
            query = """
                SELECT block_number, transaction_id, version, 
                       value_satoshis, timestamp, fee
                FROM base_bitcoin_transactions 
                WHERE block_number = %s;
            """
            
            self.db.cursor.execute(query, (block_number,))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying Bitcoin transactions for block {block_number}: {e}")
            return []
    
    def query_recent_bitcoin_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Query recent Bitcoin transactions.
        """
        try:
            query = """
                SELECT block_number, transaction_id, version, 
                       value_satoshis, timestamp, fee
                FROM base_bitcoin_transactions 
                ORDER BY timestamp DESC 
                LIMIT %s;
            """
            
            self.db.cursor.execute(query, (limit,))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying recent Bitcoin transactions: {e}")
            return []
    
    def query_recent_bitcoin_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Query recent Bitcoin transactions.
        Uses timestamp index for efficient sorting.
        """
        try:
            self.db.cursor.execute("""
                SELECT block_number, transaction_id, version, 
                       value_satoshis, timestamp, fee
                FROM base_bitcoin_transactions 
                ORDER BY timestamp DESC 
                LIMIT %s
            """, (limit,))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying recent Bitcoin transactions: {e}")
            return []

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

    def query_address_history(self, network: str, address: str, start_time: int, end_time: int) -> List[Dict[str, Any]]:
        """
        Query transaction history for an address using covering indexes.
        """
        try:
            self.db.cursor.execute("""
                SELECT block_number, transaction_hash, from_address, to_address, 
                       value_wei, timestamp
                FROM base_evm_transactions
                WHERE network = %s 
                AND timestamp BETWEEN %s AND %s
                AND (from_address = %s OR to_address = %s)
                ORDER BY timestamp DESC
            """, (network, start_time, end_time, address, address))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying address history: {e}")
            return []

    def query_daily_stats(self, network: str, start_date: datetime) -> List[Dict[str, Any]]:
        """
        Query daily transaction statistics using the materialized view.
        """
        try:
            self.db.cursor.execute("""
                SELECT network, day, tx_count, total_value
                FROM mv_daily_transactions
                WHERE network = %s AND day >= %s
                ORDER BY day DESC
            """, (network, start_date))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying daily stats: {e}")
            return []