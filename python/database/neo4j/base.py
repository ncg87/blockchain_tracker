import neo4j
from config import Settings
import logging
import os

logger = logging.getLogger(__name__)

class Neo4jDB:
    """
    Neo4j Database class.
    """
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="password", schema_file="schema.cypher"):
        """
        Initialize the Neo4j database connection.
        """
        self.driver = neo4j.GraphDatabase.driver(uri, auth=(user, password))
        self.logger = logger
        self.logger.info("Neo4jDB initialized")
        
        schema_file = os.path.join(os.path.dirname(__file__), schema_file)
        self._apply_schema(schema_file)

    def _apply_schema(self, schema_file):
        """
        Apply the schema to the database.
        """
        self.logger.info(f"Applying schema from {schema_file}")
        try:
            with open(schema_file, 'r') as file:
                schema_commands = file.read()
            
            # Split commands on semicolon, filter out empty lines and comments
            commands = [
                cmd.strip() for cmd in schema_commands.split(';')
                if cmd.strip() and not cmd.strip().startswith('//')
            ]
            
            with self.driver.session() as session:
                for command in commands:
                    session.run(command)
            
            self.logger.info("Schema applied successfully.")
        except FileNotFoundError:
            self.logger.error(f"Schema file not found at {schema_file}")
            raise
        except Exception as e:
            self.logger.error(f"Error applying schema: {e}")
            raise

    def close(self):
        """
        Close the database connection.
        """
        self.driver.close()
        self.logger.info("Neo4jDB closed")