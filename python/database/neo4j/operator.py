from .base import Neo4jDB
from .insert_ops import Neo4jInsertOps
from .query_ops import Neo4jQueryOps

class Neo4jOperator:
    def __init__(self, db: Neo4jDB):
        self.db = db
        self.insert_ops = Neo4jInsertOps(self.db)
        self.query_ops = Neo4jQueryOps(self.db)