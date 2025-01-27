from .base import MongoDatabase
from .query_ops import MongoQueryOperations
from .insert_ops import MongoInsertOperations

class MongoDBOperator:
    def __init__(self, db: MongoDatabase):
        self.db = db
        self.query = MongoQueryOperations(self.db)
        self.insert = MongoInsertOperations(self.db)

