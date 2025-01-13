from datetime import datetime
from psycopg2.extras import execute_values, execute_batch
from typing import List, Dict, Any
from .base import SQLDatabase
import json

class SQLInsertOperations:
    def __init__(self, db: SQLDatabase):
        self.db = db
        # Configure the cursor for optimal bulk inserts
        self.db.cursor.execute("SET synchronous_commit = OFF")
        self.db.cursor.execute("SET work_mem = '1GB'")

    def insert_block(self, network, block_number, block_hash, parent_hash, timestamp):
        """
        Insert a block into the PostgreSQL database.
        The table is partitioned by network, so network must be provided.
        """
        try:
            self.db.logger.info(f"Inserting {network} block {block_number} into PostgreSQL database")
            
            self.db.cursor.execute("""
                INSERT INTO blocks (network, block_number, block_hash, parent_hash, timestamp)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (network, block_number, id) DO NOTHING
            """, (network, block_number, block_hash, parent_hash, timestamp))
            self.db.conn.commit()

            self.db.logger.info(f"{network} block {block_number} inserted successfully")
        except Exception as e:
            self.db.logger.error(f"Error inserting {network} block {block_number}: {e}")
            self.db.conn.rollback()
        
    def insert_bulk_evm_transactions(self, network: str, transactions: List[Dict[str, Any]], block_number: int):
        """
        Bulk insert EVM transactions into the PostgreSQL database.
        Uses execute_values for better performance with partitioned tables.
        """
        try:
            self.db.logger.info(f"Inserting {len(transactions)} {network} transactions into PostgreSQL database in bulk from block {block_number}.")
            
            insert_query = """
                INSERT INTO base_evm_transactions 
                (block_number, network, transaction_hash, chain_id, from_address, to_address, value_wei, total_gas, timestamp)
                VALUES %s
                ON CONFLICT (network, timestamp, transaction_hash) DO NOTHING
            """

            # Use page_size for better memory management with large datasets
            execute_values(self.db.cursor, insert_query, transactions, page_size=1000)
            self.db.conn.commit()

            self.db.logger.info(f"{len(transactions)} {network} transactions inserted successfully in bulk.")
        except Exception as e:
            self.db.logger.error(f"Error inserting bulk {network} transactions: {e}")
            self.db.conn.rollback()

    def insert_bulk_bitcoin_transactions(self, transactions: List[Dict[str, Any]], block_number: int):
        """
        Bulk insert Bitcoin transactions into the PostgreSQL database.
        Table is partitioned by timestamp.
        """
        try:
            self.db.logger.info(f"Inserting Bitcoin transaction {block_number} into PostgreSQL database in bulk.")
            
            insert_query = """
                INSERT INTO base_bitcoin_transactions 
                (block_number, transaction_id, version, value_satoshis, timestamp, fee)
                VALUES %s
                ON CONFLICT (timestamp, transaction_id) DO NOTHING
            """
            
            execute_values(self.db.cursor, insert_query, transactions, page_size=1000)
            self.db.conn.commit()

            self.db.logger.info(f"{len(transactions)} Bitcoin transactions inserted successfully in bulk.")
        except Exception as e:
            self.db.logger.error(f"Error inserting bulk Bitcoin transactions: {e}")
            self.db.conn.rollback()

    def insert_bulk_xrp_transactions(self, transactions: List[Dict[str, Any]], block_number: int):
        """
        Bulk insert XRP transactions into the PostgreSQL database.
        Table is partitioned by timestamp.
        """
        try:
            self.db.logger.info(f"Inserting XRP transaction {block_number} into PostgreSQL database in bulk.")
            
            insert_query = """
                INSERT INTO base_xrp_transactions 
                (block_number, transaction_hash, account, type, fee, timestamp)
                VALUES %s
                ON CONFLICT (timestamp, transaction_hash) DO NOTHING
            """
            
            execute_values(self.db.cursor, insert_query, transactions, page_size=1000)
            self.db.conn.commit()
            
            self.db.logger.info(f"{len(transactions)} XRP transactions inserted successfully in bulk.")
        except Exception as e:
            self.db.logger.error(f"Error inserting bulk XRP transactions: {e}")
            self.db.conn.rollback()

    def insert_bulk_solana_transactions(self, transactions: List[Dict[str, Any]], block_number: int):
        """
        Bulk insert Solana transactions into the PostgreSQL database.
        Table is partitioned by timestamp.
        """
        try:
            self.db.logger.info(f"Inserting Solana transaction {block_number} into PostgreSQL database in bulk.")
            
            insert_query = """
                INSERT INTO base_solana_transactions 
                (block_number, signature, value_lamports, fee_lamports, account_key, timestamp)
                VALUES %s
                ON CONFLICT (timestamp, signature) DO NOTHING
            """
            
            execute_values(self.db.cursor, insert_query, transactions, page_size=1000)
            self.db.conn.commit()

            self.db.logger.info(f"{len(transactions)} Solana transactions inserted successfully in bulk.")
        except Exception as e:
            self.db.logger.error(f"Error inserting bulk Solana transactions: {e}")
            self.db.conn.rollback()

    def refresh_materialized_views(self):
        """
        Refresh materialized views after significant data changes
        """
        try:
            self.db.cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_transactions")
            self.db.conn.commit()
        except Exception as e:
            self.db.logger.error(f"Error refreshing materialized view: {e}")
            self.db.conn.rollback()
            
    def insert_ethereum_event(self, event_signature):
        """
        Insert an Ethereum event into the PostgreSQL database.
        """
        try:
            self.db.logger.info(f"Inserting Ethereum event {event_signature} into PostgreSQL database")
            insert_query = """
                INSERT INTO ethereum_known_events (signature_hash, name, full_signature, input_types, indexed_inputs, inputs)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (signature_hash) DO NOTHING
            """
            self.db.cursor.execute(insert_query, (
                event_signature.signature_hash,
                event_signature.name,
                event_signature.full_signature,
                json.dumps(event_signature.input_types),
                json.dumps(event_signature.indexed_inputs),
                json.dumps(event_signature.inputs)
            ))
            self.db.conn.commit()
        except Exception as e:
            self.db.logger.error(f"Error inserting Ethereum event: {e} - {event_signature}")
            self.db.conn.rollback()
        
    def insert_ethereum_contract_abi(self, contract_address: str, abi: str):
        """
        Insert an Ethereum contract ABI into the PostgreSQL database.
        """
        try:
            #self.db.logger.info(f"Inserting Ethereum contract ABI {abi} for contract {contract_address} into PostgreSQL database")
            insert_query = """
                INSERT INTO ethereum_contract_abis (contract_address, abi)
                VALUES (%s, %s)
                ON CONFLICT (contract_address) DO NOTHING
            """
            self.db.cursor.execute(insert_query, (contract_address, json.dumps(abi)))
            self.db.conn.commit()
        except Exception as e:
            self.db.logger.error(f"Error inserting Ethereum contract ABI: {e} - {abi} for contract {contract_address}")
            self.db.conn.rollback()









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