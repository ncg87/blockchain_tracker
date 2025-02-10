from typing import List, Dict, Any, Optional
from .base import ClickHouseDB
from .insert_ops import ClickHouseInsertOperations
from .query_ops import ClickHouseQueryOperations
import logging

logger = logging.getLogger(__name__)

class ClickHouseOperator:
    """
    ClickHouse Operator class that provides a unified interface for database operations.
    Similar to SQLQueryOperations but optimized for ClickHouse.
    """
    def __init__(self, db: ClickHouseDB):
        self.db = db
        self.insert = ClickHouseInsertOperations(self.db)
        self.query = ClickHouseQueryOperations(self.db)

    def get_connection(self):
        """
        Get the ClickHouse connection.
        """
        return self.db.get_connection()

    def close(self):
        """
        Close the ClickHouse connection.
        """
        self.db.close()

    def __del__(self):
        """
        Ensure proper cleanup on object deletion.
        """
        self.close()