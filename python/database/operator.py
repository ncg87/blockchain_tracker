from .mongodb.operator import MongoDBOperator
from .sql.operator import SQLOperator
from .clickhouse.operator import ClickHouseOperator, ClickHouseDB

class DatabaseOperator:
    def __init__(self, sql_db: str, mongo_db: str):
        self.sql_db = sql_db
        self.mongo_db = mongo_db
        self.clickhouse_db = ClickHouseDB()
        self.sql = SQLOperator(self.sql_db)
        self.mongodb = MongoDBOperator(self.mongo_db)
        self.clickhouse = ClickHouseOperator(self.clickhouse_db)
        
        
