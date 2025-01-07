import sqlite3
import logging
import os

logger = logging.getLogger(__name__)

class Database:
    """
    Database class.
    """
    def __init__(self, db_name="blockchain_data.db", schema_file="schema.sql"):
        """
        Initialize the database.
        """
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.logger = logger
        
        schema_file = os.path.join(os.path.dirname(__file__), schema_file)
        self._apply_schema(schema_file)

    def _apply_schema(self, schema_file):
        """
        Apply the schema to the database.
        """
        self.logger.info(f"Applying schema from {schema_file}")
        try:
            with open(schema_file, 'r') as f:
                schema = f.read()
            self.cursor.executescript(schema)
            self.conn.commit()
            self.logger.info("Schema applied successfully.")
        except Exception as e:
            self.logger.error(f"Error applying schema: {e}")
            raise

    def close(self):
        """
        Close the database connection.
        """
        self.conn.close()
