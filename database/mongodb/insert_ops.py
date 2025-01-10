import gzip
import logging
from .base import MongoDatabase
import json

class MongoInsertOperations:
    def __init__(self, mongodb: MongoDatabase):
        self.mongodb = mongodb
        self.logger = logging.getLogger(__name__)

    def _compress_data(self, block_data):
        """
        Compress block data using gzip.
        """
        try:
            json_str = json.dumps(block_data)
            compressed_data = gzip.compress(json_str.encode('utf-8'))
            return compressed_data
        except Exception as e:
            self.logger.error(f"Error compressing block data: {e}")
            raise

    def insert_block(self, block_data, network, block_number, timestamp):
        """
        Insert a compressed block into the MongoDB collection with basic metadata.
        :param block_data: The raw block data as a JSON/dict string.
        :param block_number: The block number.
        :param timestamp: The block's timestamp.
        :param network: The blockchain network name (collection name).
        """
        try:
            
            # Decode block number and timestamp
            block_number = decode_hex(block_number)
            timestamp = decode_hex(timestamp)
            # Validate inputs
            if not network or not isinstance(network, str):
                raise ValueError("Invalid network name provided for MongoDB collection.")

            # Retrieve the collection for the network
            collection = self.mongodb.get_collection(network)

            # Compress the block data
            compressed_data = self._compress_data(block_data)

            # Insert document into MongoDB
            document = {
                "block_number": block_number,
                "timestamp": timestamp,
                "compressed_data": compressed_data,
            }
            collection.insert_one(document)

            self.logger.info(f"Inserted block {block_number} into {network} collection in MongoDB.")
        except Exception as e:
            self.logger.error(f"Error inserting block {block_number} into {network} collection in MongoDB: {e}")
            
def decode_hex(value):
    """
    Decode a hexadecimal string to an integer if it's an Ethereum-style integer (e.g., block numbers, gas values).
    Does not decode long hashes or other non-integer hex values.
    :param value: Hexadecimal string (e.g., '0x677df92f') or other types.
    :return: Decoded integer or original value if not a valid short hex integer.
    """
    if isinstance(value, str) and value.startswith("0x"):
        # Only decode if the hex string is short (e.g., block numbers, gas, timestamps)
        return int(value, 16)
    return value  # Return original value if not a short hex integer
