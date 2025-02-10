from clickhouse_driver import Client
import logging
import os
from config.settings import Settings

logger = logging.getLogger(__name__)

class ClickHouseDB:
    """
    ClickHouse Database class.
    """

    def __init__(self, schema_file="schema.sql"):
        """
        Initialize ClickHouse connection.
        """
        try:
            self.config = Settings.CLICKHOUSE_CONFIG
            self.client = Client(**self.config)
            self.database = self.config["database"]

            logger.info(f"Connected to ClickHouse at {self.config['host']}:{self.config['port']}")

            # Ensure database exists
            self._create_database()

            # Apply schema if necessary
            schema_file = os.path.join(os.path.dirname(__file__), schema_file)
            self._apply_schema(schema_file)
        except Exception as e:
            logger.error(f"Error connecting to ClickHouse: {e}")
            raise

    def _create_database(self):
        """
        Create the ClickHouse database if it doesn't exist.
        """
        query = f"CREATE DATABASE IF NOT EXISTS {self.database};"
        self.client.execute(query)
        logger.info(f"Database '{self.database}' ensured.")

    def _apply_schema(self, schema_file):
        """
        Apply the schema to ClickHouse.
        """
        if not os.path.exists(schema_file):
            logger.warning(f"Schema file '{schema_file}' not found. Skipping schema application.")
            return
        
        logger.info(f"Applying schema from {schema_file}")
        try:
            with open(schema_file, 'r') as f:
                schema_commands = f.read().split(';')

            for command in schema_commands:
                command = command.strip()
                if command:
                    self.client.execute(command)

            logger.info("Schema applied successfully.")
        except Exception as e:
            logger.error(f"Error applying schema: {e}")
            raise

    def get_connection(self):
        """
        Get the ClickHouse connection.
        """
        return self.client

    def close(self):
        """
        Close the ClickHouse connection.
        """
        self.client.disconnect()
        logger.info("ClickHouse connection closed.")

    def __del__(self):
        """
        Ensure proper cleanup on object deletion.
        """
        self.close()
