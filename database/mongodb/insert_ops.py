import logging
from .base import MongoDatabase

class MongoInsertOperations:
    def __init__(self, mongodb: MongoDatabase):
        self.mongodb = mongodb
        self.logger = logging.getLogger(__name__)

    def insert_block(self, block_data, network, number):
        """
        Insert a raw block into the MongoDB collection based on the network name.
        :param block_data: The block data to insert.
        :param network: The name of the blockchain network (e.g., Bitcoin, Ethereum).
        :param number: The block number to insert.
        """
        try:
            # Validate network name
            if not network or not isinstance(network, str):
                raise ValueError("Invalid network name provided for MongoDB collection.")

            # Retrieve the collection for the network
            collection = self.mongodb.get_collection(network)
            
            # Insert the block
            collection.insert_one(block_data)
            self.logger.info(f"Inserted block {number} into the {network} collection in MongoDB.")

        except Exception as e:
            self.logger.error(f"Error inserting block {number} into {network} collection in MongoDB: {e}")
