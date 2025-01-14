import gzip
import logging
from .base import MongoDatabase
import json

class MongoQueryOperations:
    def __init__(self, mongodb: MongoDatabase):
        self.mongodb = mongodb
        self.logger = logging.getLogger(__name__)

    def _decompress_data(self, compressed_data):
        """
        Decompress gzip-compressed block data.
        """
        try:
            decompressed_data = json.loads(gzip.decompress(compressed_data).decode('utf-8'))
            return decompressed_data
        except Exception as e:
            self.logger.error(f"Error decompressing block data: {e}")
            raise

    def get_block_by_number(self, network, block_number, decompress = True):
        """
        Retrieve a block by block number and decompress the raw data.
        :param block_number: The block number to query.
        :param network: The blockchain network name (collection name).
        :return: A dictionary containing block_number, timestamp, and raw block data.
        """
        try:
            # Validate network name
            if not network or not isinstance(network, str):
                raise ValueError("Invalid network name provided for MongoDB collection.")

            # Retrieve the collection for the network
            collection = self.mongodb.get_collection(network)

            # Query the block document
            document = collection.find_one({"block_number": block_number})
            if document:
                self.logger.info(f"Retrieved block {block_number} from {network} collection in MongoDB.")
                # Decompress the block data if specified
                if decompress:
                    raw_block_data = self._decompress_data(document["compressed_data"])
                    return {
                        "block_number": document["block_number"],
                        "timestamp": document["timestamp"],
                        "raw_block_data": raw_block_data,
                    }   
                else:
                    return document
            else:
                self.logger.warning(f"Block {block_number} not found in {network} collection.")
                return None
        except Exception as e:
            self.logger.error(f"Error retrieving block {block_number} from {network} collection in MongoDB: {e}")
            return None
    
    def get_recent_blocks(self, network, limit=10, decompress = True):
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

            # Logging statements
            if not block_list:
                self.logger.warning(f"No blocks found in the {network} collection.")
                return []
            self.logger.info(f"Retrieved {len(block_list)} most recent blocks from the {network} collection.")
            
            # Decompress the block data if specified
            if decompress:
                decompressed_blocks = []
                for block in block_list:
                    decompressed_blocks.append({
                        "block_number": block["block_number"],
                        "timestamp": block["timestamp"],
                        "raw_block_data": self._decompress_data(block["compressed_data"])
                    })
                return decompressed_blocks

            return block_list
        
        except Exception as e:
            self.logger.error(f"Error retrieving recent blocks from {network} collection in MongoDB: {e}")
            return []
        
    def get_evm_transactions(self, network, block_number):
        try:
            self.logger.info(f"Retrieving transactions from {network} collection in MongoDB for block {block_number}")
            collection = self.mongodb.get_collection(network)
            transactions = collection.find({"block_number": block_number})
            self.logger.info(f"Retrieved {len(transactions)} transactions from {network} collection in MongoDB for block {block_number}")
            return transactions
        except Exception as e:
            self.logger.error(f"Error retrieving transactions from {network} collection in MongoDB: {e}")
            return []

    def get_recent_transactions(self, network, limit=10):
        try:
            self.logger.info(f"Retrieving recent transactions from {network} collection in MongoDB")
            collection = self.mongodb.get_collection(network)
            transactions = collection.find().sort("timestamp", -1).limit(limit)
            self.logger.info(f"Retrieved {len(transactions)} recent transactions from {network} collection in MongoDB")
            return transactions
        except Exception as e:
            self.logger.error(f"Error retrieving recent transactions from {network} collection in MongoDB: {e}")
            return []

    def get_recent_ethereum_transactions(self, limit=10, decompress=True):
        try:
            self.logger.info(f"Retrieving recent Ethereum transactions from MongoDB")
            collection = self.mongodb.get_collection('EthereumTransactions')
            transactions = collection.find().sort("timestamp", -1).limit(limit)
            transaction_list = list(transactions)
            self.logger.info(f"Retrieved {len(transaction_list)} recent Ethereum transactions from MongoDB")
            if decompress:
                decompressed_transactions = []
                for transaction in transaction_list:
                    decompressed_transactions.append({
                        "block_number": transaction["block_number"],
                        "transaction_hash": transaction["transaction_hash"],
                        "timestamp": transaction["timestamp"],
                        "log_data": self._decompress_data(transaction["compressed_logs"])
                    })
                return decompressed_transactions
            return transaction_list
        except Exception as e:
            self.logger.error(f"Error retrieving recent Ethereum transactions from MongoDB: {e}")
            return []
