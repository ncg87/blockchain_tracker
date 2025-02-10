from typing import List, Dict, Any, Optional
from .base import ArcticDB
from .insert_ops import ArcticInsertOperations
from .query_ops import ArcticQueryOperations
import logging

logger = logging.getLogger(__name__)

class ArcticOperator:
    """
    ArcticDB Operator class that provides a unified interface for database operations.
    Uses the new arcticdb package for improved performance.
    """
    def __init__(self, db: ArcticDB):
        self.db = db
        self.insert = ArcticInsertOperations(self.db)
        self.query = ArcticQueryOperations(self.db)

    def close(self):
        """
        Close the ArcticDB connection.
        """
        if self.db:
            self.db.close()
            logger.info("ArcticDB operator closed.")

    def __enter__(self):
        """
        Context manager entry point.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point.
        """
        self.close()

    def __del__(self):
        """
        Ensure proper cleanup on object deletion.
        """
        self.close()
