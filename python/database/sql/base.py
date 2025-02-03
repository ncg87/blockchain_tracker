import psycopg2
from psycopg2 import sql, pool
import logging
import os
from config.settings import Settings

logger = logging.getLogger(__name__)

class SQLDatabase:
    """
    PostgreSQL Database class.
    """
    def __init__(self, db_name="blockchain_data", user="postgres", password="", host="localhost", port=5432, schema_file="schema.sql"):
        """
        Initialize the database.
        """
        self.db_name = db_name
        self.user = user
        self.password = password
        self.host = host
        self.port = port

        self.conn = psycopg2.connect(
            **Settings.POSTGRES_CONFIG
        )
        
        self.pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=5,
            maxconn=100,
            **Settings.POSTGRES_CONFIG
        )
        
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
            self.cursor.execute(schema)
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
        
    def get_connection(self):
        return self.pool.getconn()

    def return_connection(self, conn):
        self.pool.putconn(conn)

    def __del__(self):
        if hasattr(self, 'pool'):
            self.pool.closeall()