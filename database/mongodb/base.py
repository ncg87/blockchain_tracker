from pymongo import MongoClient
import logging
from config import Settings
logger = logging.getLogger(__name__)


# Make the host and db_name configurable from settings
class MongoDatabase:
    def __init__(self, db_name="blockchain", host="localhost", port=27017):
        self.client = MongoClient(host, port)
        self.db = self.client[db_name]
        logger.info(f"Connected to MongoDB database: {db_name}")

    def get_collection(self, collection_name):
        """
        Retrieve a collection by name.
        """
        return self.db[collection_name]

    def close(self):
        """
        Close the MongoDB connection.
        """
        self.client.close()
        logger.info("MongoDB connection closed.")
