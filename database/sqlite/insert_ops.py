from datetime import datetime
from .base import SQLiteDatabase

class SQLiteInsertOperations:
    def __init__(self, db: SQLiteDatabase):
        self.db = db

    def insert_block(self, network, block_number, block_hash, parent_hash, timestamp):
        """
        Insert a block into the database, converting the timestamp to SQL-compatible format if necessary.
        """
        try:
            self.db.logger.info(f"Inserting {network} block {block_number} into SQL database")
            
            # Insert block into the database
            self.db.cursor.execute("""
                INSERT INTO blocks (network, block_number, block_hash, parent_hash, timestamp)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (block_hash) DO NOTHING
            """, (network, block_number, block_hash, parent_hash, timestamp))
            self.db.conn.commit()

            self.db.logger.info(f"{network} block {block_number} inserted successfully")
        except Exception as e:
            self.db.logger.error(f"Error inserting {network} block {block_number}: {e}")
        
    def insert_bulk_evm_transactions(self, network, transactions, block_number):
        """
        Bulk insert EVM transactions into the database.
        """
        try:
            self.db.logger.info(f"Inserting {network} transactions {block_number} into SQL database in bulk.")
        
            
            self.db.cursor.executemany("""
                INSERT INTO base_evm_transactions (block_number, network, transaction_hash, chain_id, from_address, to_address, value_wei, total_gas, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (transaction_hash) DO NOTHING
            """, transactions)
            self.db.conn.commit()

            self.db.logger.info(f"{len(transactions)} {network} transactions inserted successfully in bulk.")
        except Exception as e:
            self.db.logger.error(f"Error inserting bulk {network} transactions: {e}")
    
    def insert_bulk_bitcoin_transactions(self, transactions, block_number):
        """
        Bulk insert Bitcoin transactions into the database.
        """
        try:
            self.db.logger.info(f"Inserting Bitcoin transaction {block_number} into SQL database in bulk.")
            
            self.db.cursor.executemany("""
                INSERT INTO base_bitcoin_transactions (block_number, transaction_id, version, value_satoshis, timestamp, fee)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (transaction_id) DO NOTHING
            """, transactions)
            self.db.conn.commit()

            self.db.logger.info(f"{len(transactions)} Bitcoin transactions inserted successfully in bulk.")
        except Exception as e:
            self.db.logger.error(f"Error inserting bulk Bitcoin transactions: {e}")

    def insert_bulk_xrp_transactions(self, transactions, block_number):
        """
        Bulk insert XRP transactions into the database.
        """
        try:
            self.db.logger.info(f"Inserting XRP transaction {block_number} into SQL database in bulk.")
            
            self.db.cursor.executemany("""
                INSERT INTO base_xrp_transactions (block_number, transaction_hash, account, type, fee, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (transaction_hash) DO NOTHING
            """, transactions)
            self.db.conn.commit()
            
            self.db.logger.info(f"{len(transactions)} XRP transactions inserted successfully in bulk.")
        except Exception as e:
            self.db.logger.error(f"Error inserting bulk XRP transactions: {e}")

    def insert_bulk_solana_transactions(self, transactions, block_number):
        """
        Bulk insert Solana transactions into the database.
        """
        try:
            self.db.logger.info(f"Inserting Solana transaction {block_number} into SQL database in bulk.")
            
            self.db.cursor.executemany("""
                INSERT INTO base_solana_transactions (block_number, signature, value_lamports, fee_lamports, account_key, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (signature) DO NOTHING
            """, transactions)
            self.db.conn.commit()

            self.db.logger.info(f"{len(transactions)} Solana transactions inserted successfully in bulk.")
        except Exception as e:
            self.db.logger.error(f"Error inserting bulk Solana transactions: {e}")

# add in future to reduce total code
def convert_timestamp(timestamp):
    """
    Convert a timestamp to a SQL-compatible DATETIME format.
    """
    
    # Convert timestamp to SQL-compliant DATETIME format
    if isinstance(timestamp, int):  # If given as UNIX time
        timestamp = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(timestamp, str):  # If already a string, assume it's correct
        # Optionally, validate the format
        try:
            datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            raise ValueError("Timestamp string is not in '%Y-%m-%d %H:%M:%S' format")
    elif isinstance(timestamp, datetime):  # If given as a datetime object
        timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
    else:
        raise TypeError("Invalid timestamp format. Must be int (UNIX), str, or datetime object.")
    return timestamp
