from .base import SQLDatabase
from datetime import datetime

class SQLQueryOperations:
    """
    Query operations class.
    """
    def __init__(self, db: SQLDatabase):
        self.db = db

    def query_blocks_by_time(self, start_time, end_time):
        """
        Query blocks within a specified time range.
        :param start_time: Start of the range (datetime object or string in '%Y-%m-%d %H:%M:%S' format).
        :param end_time: End of the range (datetime object or string in '%Y-%m-%d %H:%M:%S' format).
        :return: List of blocks in the range.
        """
        try:
            # Ensure time is in the correct SQL-compliant format
            if isinstance(start_time, datetime):
                start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
            if isinstance(end_time, datetime):
                end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')

            self.db.logger.info(f"Querying blocks between {start_time} and {end_time} from SQL database")

            self.db.cursor.execute("""
                SELECT * FROM blocks
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp ASC
            """, (start_time, end_time))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying blocks by time: {e}")
            return []
    
    def query_blocks(self, limit=10):
        try:
            self.db.cursor.execute("""
                SELECT * FROM blocks ORDER BY block_number DESC LIMIT ?
            """, (limit,))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying blocks: {e}")
            return []
    
    def query_by_network(self, network, block_number=None):
        """
        Query block(s) for a specific network. Optionally filter by block number.
        :param network: The blockchain network (e.g., 'Ethereum', 'Bitcoin').
        :param block_number: The specific block number to query (optional).
        :return: List of blocks matching the criteria.
        """
        try:
            self.db.logger.info(f"Querying blocks for network {network} with block_number={block_number} from SQL database")
            
            if block_number is not None:
                # Query for a specific block in the network
                self.db.cursor.execute("""
                    SELECT * FROM blocks
                    WHERE network = ? AND block_number = ?
                """, (network, block_number))
            else:
                # Query for all blocks in the network
                self.db.cursor.execute("""
                    SELECT * FROM blocks
                    WHERE network = ?
                    ORDER BY block_number DESC
                """, (network,))
            
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying blocks for network {network} from SQL database: {e}")
            return []
        
    def query_evm_transactions(self, network, block_number):
        try:
            self.db.cursor.execute("""
                SELECT * FROM base_env_transactions WHERE network = ? AND block_number = ?
            """, (network, block_number))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying transactions for network {network} from SQL database: {e}")
            return []

