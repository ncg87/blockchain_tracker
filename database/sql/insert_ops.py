from datetime import datetime
from .base import SQLDatabase

class SQLInsertOperations:
    def __init__(self, db: SQLDatabase):
        self.db = db

    def insert_block(self, block):
        """
        Insert a block into the database, converting the timestamp to SQL-compatible format if necessary.
        """
        try:
            self.db.logger.info(f"Inserting {block['network']} block {block['block_number']} into SQL database")
            
            # Insert block into the database
            self.db.cursor.execute("""
                INSERT INTO blocks (network, block_number, block_hash, parent_hash, timestamp)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (block_hash) DO NOTHING
            """, (block['network'], block['block_number'], block['block_hash'], block['parent_hash'], block['timestamp']))
            self.db.conn.commit()

            self.db.logger.info(f"Block {block['block_number']} inserted successfully")
        except Exception as e:
            self.db.logger.error(f"Error inserting block {block['block_number']}: {e}")

    def insert_evm_transaction(self, network, transaction):
        """
        Insert a transaction into the database.
        """
        try:
            self.db.logger.debug(f"Inserting {network} transaction {transaction['transaction_hash']} into SQL database")
            
            # Insert transaction into the database
            self.db.cursor.execute("""
                INSERT INTO base_evm_transactions (block_number, network, transaction_hash, chain_id, from_address, to_address, value_wei, total_gas, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (transaction_hash) DO NOTHING
            """, (transaction['block_number'], network, transaction['transaction_hash'], transaction['chain_id'], transaction['from_address'], transaction['to_address'], transaction['amount'], transaction['gas_costs'], transaction['timestamp']))
            self.db.conn.commit()

            self.db.logger.debug(f"Transaction {transaction['transaction_hash']} inserted successfully")
        except Exception as e:
            self.db.logger.error(f"Error inserting transaction {transaction['transaction_hash']}: {e}")

    def insert_bitcoin_transaction(self, transaction):
        """
        Insert a bitcoin transaction into the database.
        """
        try:
            self.db.logger.debug(f"Inserting bitcoin transaction {transaction['transaction_id']} into SQL database")
            self.db.cursor.execute("""
                INSERT INTO base_bitcoin_transactions (block_number, transaction_id, version, value_satoshis, timestamp, fee    )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (transaction_id) DO NOTHING
            """, (transaction['block_number'], transaction['transaction_id'], transaction['version'], transaction['value_satoshis'], transaction['timestamp'], transaction.get('fee', 0)))
            self.db.conn.commit()

            self.db.logger.debug(f"Transaction {transaction['transaction_id']} inserted successfully")
        except Exception as e:
            self.db.logger.error(f"Error inserting transaction {transaction['transaction_id']}: {e}")
            
    def insert_bulk_evm_transactions(self, network, transactions, block_number):
        """
        Bulk insert EVM transactions into the database.
        """
        try:
            self.db.logger.debug(f"Inserting {network} transactions {block_number} into SQL database in bulk.")
        
            
            self.db.cursor.executemany("""
                INSERT INTO base_evm_transactions (block_number, network, transaction_hash, chain_id, from_address, to_address, value_wei, total_gas, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (transaction_hash) DO NOTHING
            """, transactions)
            self.db.conn.commit()

            self.db.logger.debug(f"{len(transactions)} {network} transactions inserted successfully in bulk.")
        except Exception as e:
            self.db.logger.error(f"Error inserting bulk {network} transactions: {e}")
    
    def insert_bulk_bitcoin_transactions(self, transactions, block_number):
        """
        Bulk insert Bitcoin transactions into the database.
        """
        try:
            self.db.logger.debug(f"Inserting Bitcoin transaction {block_number} into SQL database in bulk.")
            
            self.db.cursor.executemany("""
                INSERT INTO base_bitcoin_transactions (block_number, transaction_id, version, value_satoshis, timestamp, fee)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (transaction_id) DO NOTHING
            """, transactions)
            self.db.conn.commit()

            self.db.logger.debug(f"{len(transactions)} Bitcoin transactions inserted successfully in bulk.")
        except Exception as e:
            self.db.logger.error(f"Error inserting bulk Bitcoin transactions: {e}")

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
