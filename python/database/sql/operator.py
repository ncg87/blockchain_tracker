from .base import SQLDatabase
from .operations import SQLQueryOperations, SQLInsertOperations

class SQLOperator:
    def __init__(self, db: SQLDatabase):
        self.db = db
        self.query = SQLQueryOperations(self.db)
        self.insert = SQLInsertOperations(self.db)