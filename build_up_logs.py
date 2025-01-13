from config import Settings
from chains import EthereumQuerier, EthereumProcessor, EthereumPipeline
from database import SQLDatabase, MongoDatabase, MongoQueryOperations
import logging

querier = EthereumQuerier()
sql_database = SQLDatabase()
mongodb_database = MongoDatabase()
processor = EthereumProcessor(sql_database, mongodb_database, querier)

mongo_query_ops = MongoQueryOperations(mongodb_database)
query = mongo_query_ops.get_recent_blocks('Ethereum', 1000)


for block in query:
    for i in range(5):
        processor.process_logs(block['block_number'], block['timestamp'])
