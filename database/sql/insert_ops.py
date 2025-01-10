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

            # Convert timestamp to SQL-compliant DATETIME format
            if isinstance(block['timestamp'], int):  # If given as UNIX time
                block['timestamp'] = datetime.utcfromtimestamp(block['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(block['timestamp'], str):  # If already a string, assume it's correct
                # Optionally, validate the format
                try:
                    datetime.strptime(block['timestamp'], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    raise ValueError("Timestamp string is not in '%Y-%m-%d %H:%M:%S' format")
            elif isinstance(block['timestamp'], datetime):  # If given as a datetime object
                block['timestamp'] = block['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                raise TypeError("Invalid timestamp format. Must be int (UNIX), str, or datetime object.")

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
                INSERT INTO base_env_transactions (block_number, network, transaction_hash, chain_id, from_address, to_address, amount, gas_costs, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (transaction_hash) DO NOTHING
            """, (transaction['block_number'], network, transaction['transaction_hash'], transaction['chain_id'], transaction['from_address'], transaction['to_address'], transaction['amount'], transaction['gas_costs'], transaction['timestamp']))
            self.db.conn.commit()

            self.db.logger.debug(f"Transaction {transaction['transaction_hash']} inserted successfully")
        except Exception as e:
            self.db.logger.error(f"Error inserting transaction {transaction['transaction_hash']}: {e}")
