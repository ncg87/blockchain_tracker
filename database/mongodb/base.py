from pymongo import MongoClient
import logging

logger = logging.getLogger(__name__)

class MongoDatabase:
    def __init__(self, db_name="blockchain", host="localhost", port=27017):
        self.client = MongoClient(host, port)
        self.db = self.client[db_name]
        logger.info(f"Connected to MongoDB database: {db_name}")
        
        # Ensure indexes are created
        self._create_indexes()

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

    def _create_indexes(self):
        """
        Create necessary indexes for all collections.
        """
        try:
            # Make this a .env file variable
            collections_to_index = ["Solana", "Bitcoin", "Ethereum", "BNB", "XRP"]  # Add network names here
            for collection_name in collections_to_index:
                collection = self.get_collection(collection_name)
                
                # Create indexes
                collection.create_index("block_number", unique=True)
                collection.create_index("timestamp")  # For potential TTL or queries by time
                logger.info(f"Indexes created for collection: {collection_name}")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")