from datetime import datetime
from database import Database

class InsertOperations:
    def __init__(self, db: Database):
        self.db = db

    def insert_block(self, block):
        """
        Insert a block into the database, converting the timestamp to SQL-compatible format if necessary.
        """
        try:
            self.db.logger.info(f"Inserting block {block['block_number']} into database")

            # Convert timestamp to SQL-compliant DATETIME format
            if isinstance(block['timestamp'], int):  # If given as UNIX time
                block['timestamp'] = datetime.utcfromtimestamp(block['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(block['timestamp'], str):  # If already a string, assume it's correct
                # Optionally, validate the format
                try:
                    datetime.strptime(block['timestamp'], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    raise ValueError("Timestamp string is not in '%Y-%m-%d %H:%M:%S' format")
            elif isinstance(block['timestamp'], datetime):  # If given as a datetime object
                block['timestamp'] = block['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                raise TypeError("Invalid timestamp format. Must be int (UNIX), str, or datetime object.")

            # Insert block into the database
            self.db.cursor.execute("""
                INSERT INTO blocks (network, block_number, block_hash, parent_hash, timestamp, block_data)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (block_hash) DO NOTHING
            """, (block['network'], block['block_number'], block['block_hash'], block['parent_hash'], block['timestamp'], block['block_data']))
            self.db.conn.commit()

            self.db.logger.info(f"Block {block['block_number']} inserted successfully")
        except Exception as e:
            self.db.logger.error(f"Error inserting block {block['block_number']}: {e}")
