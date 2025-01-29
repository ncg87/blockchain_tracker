from datetime import datetime
from typing import List, Dict, Any
from .base import SQLDatabase
from .operations import BlockInsertOperations, EVMInsertOperations, BitcoinInsertOperations, SolanaInsertOperations, XRPInsertOperations

class SQLInsertOperations:
    def __init__(self, db: SQLDatabase):
        self.db = db
        # Configure the cursor for optimal bulk inserts
        self.db.cursor.execute("SET synchronous_commit = OFF")
        self.db.cursor.execute("SET work_mem = '1GB'")
        self.block = BlockInsertOperations(self.db)
        self.evm = EVMInsertOperations(self.db)
        self.bitcoin = BitcoinInsertOperations(self.db)
        self.solana = SolanaInsertOperations(self.db)
        self.xrp = XRPInsertOperations(self.db)

    def insert_block(self, network, block_number, block_hash, parent_hash, timestamp):
        return self.block.insert_block(network, block_number, block_hash, parent_hash, timestamp)
        
    def insert_bulk_bitcoin_transactions(self, transactions: List[Dict[str, Any]], block_number: int):
        return self.bitcoin.insert_transactions(transactions, block_number)

    def insert_bulk_xrp_transactions(self, transactions: List[Dict[str, Any]], block_number: int):
        return self.xrp.insert_transactions(transactions, block_number)

    def insert_bulk_solana_transactions(self, transactions: List[Dict[str, Any]], block_number: int):
        return self.solana.insert_transactions(transactions, block_number)

    def insert_evm_event(self, network: str, event_object) -> bool:
        return self.evm.insert_event(network, event_object)

def convert_timestamp(timestamp):
    """
    Convert a timestamp to a PostgreSQL-compatible TIMESTAMP format.
    """
    if isinstance(timestamp, int):  # If given as UNIX time
        timestamp = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(timestamp, str):  # If already a string, assume it's correct
        try:
            datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            raise ValueError("Timestamp string is not in '%Y-%m-%d %H:%M:%S' format")
    elif isinstance(timestamp, datetime):  # If given as a datetime object
        timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    else:
        raise TypeError("Invalid timestamp format. Must be int (UNIX), str, or datetime object.")
    return timestamp