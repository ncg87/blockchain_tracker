import gzip
import logging
from .base import MongoDatabase
import json
from pymongo.errors import BulkWriteError

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
            return None

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
            if compressed_data is None:
                return


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
    
    def insert_evm_transactions(self, transactions, network, block_number, timestamp):
        """
        Bulk insert for EVM transactions, skipping any that fail compression.
        """
        collection = self.mongodb.get_collection(f'{network}Transactions')
        
        # Filter and prepare documents, skipping any compression failures
        documents = []
        for tx_hash, logs in transactions.items():
            if not logs:
                continue
            
            try:
                compressed_data = self._compress_data(logs)
                if compressed_data is None:
                    continue
                documents.append({
                    "block_number": block_number,
                    "timestamp": timestamp,
                    "network": network,
                    "transaction_hash": tx_hash,
                    "compressed_logs": compressed_data
                })
            except Exception as e:
                self.logger.debug(f"Error compressing block data: {str(e)}")
                continue  # Skip any compression failures
        
        if not documents:
            return
        
        try:
            # Bulk insert only the successfully compressed documents
            result = collection.insert_many(documents, ordered=False)
            self.logger.info(
                f"Block {block_number} bulk insert stats for {network}: "
                f"Inserted: {len(result.inserted_ids)}, "
                f"Total Processed: {len(transactions)}"
            )
            
        except Exception as e:
            self.logger.debug(f"Error during bulk insert for block {block_number}: {str(e)}")

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
