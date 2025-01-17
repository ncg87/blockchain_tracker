from .base import SQLDatabase
from datetime import datetime
from typing import List, Optional, Dict, Any
from psycopg2.extras import RealDictCursor
from dataclasses import dataclass
import json
class SQLQueryOperations:
    """
    Query operations class optimized for PostgreSQL.
    """
    def __init__(self, db: SQLDatabase):
        self.db = db
        # Use RealDictCursor for more convenient dictionary access
        self.db.cursor = self.db.conn.cursor(cursor_factory=RealDictCursor)

    def query_blocks_by_time(self, start_time: int, end_time: int) -> List[Dict[str, Any]]:
        """
        Query blocks within a specified time range.
        """
        try:
            self.db.logger.info(f"Querying blocks between {start_time} and {end_time}")

            query = """
                SELECT id, network, block_number, block_hash, parent_hash, timestamp 
                FROM blocks 
                WHERE timestamp BETWEEN %s AND %s
                ORDER BY timestamp ASC;
            """
            
            self.db.cursor.execute(query, (start_time, end_time))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying blocks by time: {e}")
            return []
    
    def query_blocks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Query recent blocks across all networks.
        """
        try:
            query = """
                SELECT id, network, block_number, block_hash, parent_hash, timestamp
                FROM blocks 
                ORDER BY block_number DESC 
                LIMIT %s;
            """
            
            self.db.cursor.execute(query, (limit,))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying blocks: {e}")
            return []
    
    def query_by_network(self, network: str, block_number: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Query block(s) for a specific network.
        """
        try:
            self.db.logger.info(f"Querying blocks for network {network} with block_number={block_number}")
            
            if block_number is not None:
                query = """
                    SELECT id, network, block_number, block_hash, parent_hash, timestamp
                    FROM blocks
                    WHERE network = %s AND block_number = %s;
                """
                self.db.cursor.execute(query, (network, block_number))
            else:
                query = """
                    SELECT id, network, block_number, block_hash, parent_hash, timestamp
                    FROM blocks
                    WHERE network = %s
                    ORDER BY block_number DESC
                    LIMIT 1000;
                """
                self.db.cursor.execute(query, (network,))
            
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying blocks for network {network}: {e}")
            return []
        
    def query_evm_transactions(self, network: str, block_number: int) -> List[Dict[str, Any]]:
        """
        Query EVM transactions for a specific block.
        """
        try:
            query = """
                SELECT block_number, network, transaction_hash, chain_id, 
                       from_address, to_address, value_wei, total_gas, timestamp
                FROM base_evm_transactions 
                WHERE network = %s AND block_number = %s;
            """
            
            self.db.cursor.execute(query, (network, block_number))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying transactions for network {network}: {e}")
            return []

    def query_bitcoin_transactions(self, block_number: int) -> List[Dict[str, Any]]:
        """
        Query Bitcoin transactions for a specific block.
        """
        try:
            query = """
                SELECT block_number, transaction_id, version, 
                       value_satoshis, timestamp, fee
                FROM base_bitcoin_transactions 
                WHERE block_number = %s;
            """
            
            self.db.cursor.execute(query, (block_number,))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying Bitcoin transactions for block {block_number}: {e}")
            return []
    
    def query_recent_bitcoin_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Query recent Bitcoin transactions.
        """
        try:
            query = """
                SELECT block_number, transaction_id, version, 
                       value_satoshis, timestamp, fee
                FROM base_bitcoin_transactions 
                ORDER BY timestamp DESC 
                LIMIT %s;
            """
            
            self.db.cursor.execute(query, (limit,))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying recent Bitcoin transactions: {e}")
            return []
    
    def query_recent_bitcoin_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Query recent Bitcoin transactions.
        Uses timestamp index for efficient sorting.
        """
        try:
            self.db.cursor.execute("""
                SELECT block_number, transaction_id, version, 
                       value_satoshis, timestamp, fee
                FROM base_bitcoin_transactions 
                ORDER BY timestamp DESC 
                LIMIT %s
            """, (limit,))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying recent Bitcoin transactions: {e}")
            return []

    def query_high_value_transactions(self, network: str, min_value: int) -> List[Dict[str, Any]]:
        """
        Query high-value transactions using the partial index.
        """
        try:
            if network == 'bitcoin':
                self.db.cursor.execute("""
                    SELECT block_number, transaction_id, value_satoshis, timestamp, fee
                    FROM base_bitcoin_transactions
                    WHERE value_satoshis > %s
                    ORDER BY value_satoshis DESC
                    LIMIT 100
                """, (min_value,))
            elif network in ['ethereum', 'bsc']:
                self.db.cursor.execute("""
                    SELECT block_number, transaction_hash, from_address, to_address, 
                           value_wei, timestamp
                    FROM base_evm_transactions
                    WHERE network = %s AND value_wei > %s
                    ORDER BY value_wei DESC
                    LIMIT 100
                """, (network, min_value))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying high-value transactions: {e}")
            return []

    def query_address_history(self, network: str, address: str, start_time: int, end_time: int) -> List[Dict[str, Any]]:
        """
        Query transaction history for an address using covering indexes.
        """
        try:
            self.db.cursor.execute("""
                SELECT block_number, transaction_hash, from_address, to_address, 
                       value_wei, timestamp
                FROM base_evm_transactions
                WHERE network = %s 
                AND timestamp BETWEEN %s AND %s
                AND (from_address = %s OR to_address = %s)
                ORDER BY timestamp DESC
            """, (network, start_time, end_time, address, address))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying address history: {e}")
            return []

    def query_daily_stats(self, network: str, start_date: datetime) -> List[Dict[str, Any]]:
        """
        Query daily transaction statistics using the materialized view.
        """
        try:
            self.db.cursor.execute("""
                SELECT network, day, tx_count, total_value
                FROM mv_daily_transactions
                WHERE network = %s AND day >= %s
                ORDER BY day DESC
            """, (network, start_date))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying daily stats: {e}")
            return []

    def query_evm_event(self, network: str, signature_hash: str) -> Optional[Dict[str, Any]]:
        """
        Query an EVM event by its network and signature hash.
        """
        try:
            self.db.cursor.execute("""
                SELECT * 
                FROM evm_known_events 
                WHERE network = %s AND signature_hash = %s
            """, (network, signature_hash))
            
            result = self.db.cursor.fetchone()
            
            if result:
                return EventSignature(
                    signature_hash=result.get('signature_hash'),
                    name=result.get('name'),
                    full_signature=result.get('full_signature'),
                    input_types=json.loads(result.get('input_types')),
                    indexed_inputs=json.loads(result.get('indexed_inputs')),
                    inputs=json.loads(result.get('inputs'))
                )
            return None
        except Exception as e:
            self.db.logger.error(f"Error querying EVM event for network {network}: {e}")
            return None 
        
    def query_evm_contract_abi(self, network: str, contract_address: str) -> Optional[Dict[str, Any]]:
        """
        Query an EVM contract ABI by its network and address.
        """
        try:
            self.db.cursor.execute("""
                SELECT * 
                FROM evm_contract_abis 
                WHERE network = %s AND contract_address = %s
            """, (network, contract_address))
            return self.db.cursor.fetchone()
        except Exception as e:
            #self.db.logger.error(f"Error querying EVM contract ABI for network {network}: {e}")
            return None
        
    def query_evm_swap(self, network: str, contract_address: str) -> Optional[Dict[str, Any]]:
        """
        Query an EVM swap by its network and address.
        """
        try:
            self.db.cursor.execute("""
                SELECT address, factory_address, fee, token0_name, token1_name, name
                FROM evm_swap
                WHERE network = %s AND address = %s
            """, (network, contract_address))
            result = self.db.cursor.fetchone()
            if result:
                return ContractInfo(
                    address=result.get('address'),
                    factory=result.get('factory_address'),
                    fee=result.get('fee'),
                    token0_name=result.get('token0_name'),
                    token1_name=result.get('token1_name'),
                    name=result.get('name')
                )
            return None
        except Exception as e:
            #self.db.logger.error(f"Error querying EVM swap for network {network}: {e}")
            return None
    
    def query_evm_token_info(self, network: str, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Query an EVM token info by its network and address.
        """
        try:
            self.db.cursor.execute("""
                SELECT address, name, symbol
                FROM evm_token_info
                WHERE network = %s AND address = %s
            """, (network, token_address))
            result = self.db.cursor.fetchone()
            if result:
                return TokenInfo(
                    address=result.get('address'),
                    name=result.get('name'),
                    symbol=result.get('symbol')
                )
            return None
        except Exception as e:
            #self.db.logger.error(f"Error querying EVM token info for network {network}: {e}", exc_info=True)
            return None

@dataclass
class EventSignature:
    signature_hash: str
    name: str
    full_signature: str
    input_types: List[str]
    indexed_inputs: List[bool]
    inputs: List[dict]
    
@dataclass
class ContractInfo:
    address: str
    factory: str
    fee: int
    token0_name: str
    token1_name: str
    name: str
    
@dataclass
class TokenInfo:
    address: str
    name: str
    symbol: str
