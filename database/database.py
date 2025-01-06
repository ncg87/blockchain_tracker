import sqlite3
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_name="blockchain_data.db"):
        """
        Initialize the database connection and ensure tables exist.
        """
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self._create_tables()
        self.logger = logger

    # Change INTEGERS and all number fields to BIGINT, NUMERIC, etc when I switch to postgres
    
    def _create_tables(self):
        """
        Create the tables if they don't already exist.
        """
        # Create Blocks table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            network TEXT NOT NULL,
            block_number INTEGER NOT NULL,
            block_hash TEXT NOT NULL,
            parent_hash TEXT,
            miner TEXT,
            timestamp INTEGER NOT NULL,
            gas_limit REAL,
            gas_used REAL
        )
        """)

        # Create Transactions table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            network TEXT NOT NULL,
            block_number INTEGER NOT NULL,
            transaction_hash TEXT NOT NULL,
            from_address TEXT NOT NULL,
            to_address TEXT,
            amount REAL,
            gas REAL,
            gas_price REAL,
            input_data TEXT,
            timestamp INTEGER NOT NULL
        )
        """)

        # Create Withdrawals table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            network TEXT NOT NULL,
            block_number INTEGER NOT NULL,
            withdrawal_index INTEGER NOT NULL,
            validator_index INTEGER,
            address TEXT NOT NULL,
            amount REAL NOT NULL,
            timestamp INTEGER NOT NULL
        )
        """)
        
        # Create Contract Metadata table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS contract_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_address TEXT NOT NULL,
            network TEXT NOT NULL,
            abi TEXT,
            UNIQUE (contract_address, network)
        )
        """)

        self.conn.commit()

    def insert_block(self, block):
        """
        Insert a new block into the blocks table.
        """
        self.logger.info(f"Inserting block {block['block_number']}")
        try:
            self.cursor.execute("""
                INSERT INTO blocks (network, block_number, block_hash, parent_hash, miner, timestamp, gas_limit, gas_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (block['network'], block['block_number'], block['block_hash'], block['parent_hash'], block['miner'], block['timestamp'], block['gas_limit'], block['gas_used']))
            self.conn.commit()
            self.logger.debug(f"Block {block['block_number']} inserted successfully.")
        except Exception as e:
            self.logger.error(f"Error inserting block {block['block_number']}: {e}")

    def insert_transaction(self, transaction):
        """
        Insert a new transaction into the transactions table.
        """
        self.logger.info(f"Inserting transaction {transaction['transaction_hash']}")
        try:
            self.cursor.execute("""
            INSERT INTO transactions (network, block_number, transaction_hash, from_address, to_address, amount, gas, gas_price, input_data, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
            transaction['network'],
            transaction['block_number'],
            transaction['transaction_hash'],
            transaction['from_address'],
            transaction['to_address'],
            transaction['amount'],
            transaction['gas'],
            transaction['gas_price'],
            transaction['input_data'] if transaction['input_data'] else None,
            transaction['timestamp']))
            self.conn.commit()
            self.logger.debug(f"Transaction {transaction['transaction_hash']} inserted successfully.")
        except Exception as e:
            self.logger.error(f"Error inserting transaction {transaction['transaction_hash']}: {e}")

    def insert_withdrawal(self, withdrawal):
        """
        Insert a new withdrawal into the withdrawals table.
        """
        self.logger.info(f"Inserting withdrawal {withdrawal['withdrawal_index']}")
        try:
            self.cursor.execute("""
            INSERT INTO withdrawals (network, block_number, withdrawal_index, validator_index, address, amount, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (withdrawal['network'], withdrawal['block_number'], withdrawal['withdrawal_index'], withdrawal['validator_index'], withdrawal['address'], withdrawal['amount'], withdrawal['timestamp']))
            self.conn.commit()
            self.logger.debug(f"Withdrawal {withdrawal['withdrawal_index']} inserted successfully.")
        except Exception as e:
            self.logger.error(f"Error inserting withdrawal {withdrawal['withdrawal_index']}: {e}")

    # If new contract, insert it, and maybe check through transactions and update the input to decode it 
    def insert_contract_metadata(self, contract_address, network, abi):
        """
        Insert or update a contract's metadata.
        """
        self.logger.info(f"Inserting contract metadata for {contract_address}")
        try:
            self.cursor.execute("""
            INSERT INTO contract_metadata (contract_address, network, abi)
            VALUES (?, ?, ?)
            ON CONFLICT(contract_address, network) DO NOTHING
            """, (contract_address, network, abi))
            self.conn.commit()
            self.logger.debug(f"Contract metadata for {contract_address} inserted successfully.")
        except Exception as e:
            self.logger.error(f"Error inserting contract metadata for {contract_address}: {e}")

    def query_blocks(self, limit=10):
        """
        Query the latest blocks.
        """
        self.logger.info(f"Querying {limit} latest blocks")
        try:
            self.cursor.execute("""
            SELECT * FROM blocks ORDER BY block_number DESC LIMIT ?
            """, (limit,))
            return self.cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Error querying blocks: {e}")
            return []

    def query_transactions(self, limit=10):
        """
        Query the latest transactions.
        """
        self.logger.info(f"Querying {limit} latest transactions")
        try:
            self.cursor.execute("""
            SELECT * FROM transactions ORDER BY id DESC LIMIT ?
            """, (limit,))
            return self.cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Error querying transactions: {e}")
            return []

    def query_withdrawals(self, limit=10):
        """
        Query the latest withdrawals.
        """
        self.logger.info(f"Querying {limit} latest withdrawals")
        try:
            self.cursor.execute("""
            SELECT * FROM withdrawals ORDER BY id DESC LIMIT ?
            """, (limit,))
            return self.cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Error querying withdrawals: {e}")
            return []
    
    def query_contract_metadata(self, contract_address, network=None):
        """
        Retrieve a contract's metadata by address and optional network.
        """
        try:
            self.logger.info(f"Querying contract metadata for address: {contract_address}")
            
            if network:
                self.logger.info(f"Including network filter: {network}")
                self.cursor.execute("""
                    SELECT * FROM contract_metadata
                    WHERE contract_address = ? AND network = ?
                """, (contract_address, network))
            else:
                self.logger.info("Querying without network filter")
                self.cursor.execute("""
                    SELECT * FROM contract_metadata
                    WHERE contract_address = ?
                """, (contract_address,))

            # Fetch result
            result = self.cursor.fetchone()
            if result:
                self.logger.debug(f"Metadata found for contract {contract_address} on network {network if network else 'all networks'}")
                return result
            else:
                self.logger.warning(f"No metadata found for contract {contract_address} on network {network if network else 'all networks'}")
                return None
        except Exception as e:
            self.logger.error(f"Error querying contract metadata for address {contract_address}: {e}")
            return None

    def close(self):
        """
        Close the database connection.
        """
        self.conn.close()
