from ..base import SQLDatabase
from psycopg2.extras import RealDictCursor

class BaseOperations:
    def __init__(self, db: SQLDatabase):
        self.db = db
        self.db.cursor = self.db.conn.cursor(cursor_factory=RealDictCursor)