from database import Database

class QueryOperations:
    """
    Query operations class.
    """
    def __init__(self, db: Database):
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

            self.db.logger.info(f"Querying blocks between {start_time} and {end_time}")

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
