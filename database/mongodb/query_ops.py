import logging
from .base import MongoDatabase

class MongoQueryOperations:
    def __init__(self, mongodb: MongoDatabase):
        self.mongodb = mongodb
        self.logger = logging.getLogger(__name__)

    def get_block_by_number(self, block_number, network):
        """
        Retrieve a raw block by its block number from the appropriate collection.
        :param block_number: The block number to query.
        :param network: The name of the blockchain network.
        """
        try:
            # Validate network name
            if not network or not isinstance(network, str):
                raise ValueError("Invalid network name provided for MongoDB collection.")

            # Retrieve the collection for the network
            collection = self.mongodb.get_collection(network)

            # Query the block
            block = collection.find_one({"block_number": block_number})
            if block:
                self.logger.info(f"Retrieved block {block_number} from the {network} collection in MongoDB.")
            else:
                self.logger.warning(f"Block {block_number} not found in the {network} collection.")
            return block
        except Exception as e:
            self.logger.error(f"Error retrieving block {block_number} from {network} collection in MongoDB: {e}")
            return None
    
    def get_recent_blocks(self, network, limit=10):
        """
        Retrieve the most recent blocks from the specified blockchain network.
        :param network: The name of the blockchain network.
        :param limit: The number of recent blocks to retrieve (default: 10).
        :return: List of the most recent blocks.
        """
        try:
            # Validate network name
            if not network or not isinstance(network, str):
                raise ValueError("Invalid network name provided for MongoDB collection.")

            # Retrieve the collection for the network
            collection = self.mongodb.get_collection(network)

            # Query and sort by block_number in descending order
            recent_blocks = collection.find().sort("block_number", -1).limit(limit)
            
            # Convert to a list
            block_list = list(recent_blocks)

            if block_list:
                self.logger.info(f"Retrieved {len(block_list)} most recent blocks from the {network} collection.")
            else:
                self.logger.warning(f"No blocks found in the {network} collection.")
            
            return block_list
        except Exception as e:
            self.logger.error(f"Error retrieving recent blocks from {network} collection in MongoDB: {e}")
            return []

