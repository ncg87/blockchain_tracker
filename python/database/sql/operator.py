from .base import SQLDatabase
from .query_ops import SQLQueryOperations
from .insert_ops import SQLInsertOperations

class SQLOperator:
    def __init__(self, db: SQLDatabase):
        self.db = db
        self.query = SQLQueryOperations(self.db)
        self.insert = SQLInsertOperations(self.db)