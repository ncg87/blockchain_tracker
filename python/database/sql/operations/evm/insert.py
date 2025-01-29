from typing import List, Dict, Any
from ..base import BaseOperations
from ...queries import (
    INSERT_EVM_TRANSACTIONS, INSERT_EVM_EVENTS, INSERT_EVM_CONTRACT_ABI,
    INSERT_EVM_SWAP, INSERT_EVM_TOKEN_INFO, INSERT_EVM_CONTRACT_TO_FACTORY,
    INSERT_EVM_TRANSACTION_SWAP
)
from psycopg2.extras import execute_values
import json
class EVMInsertOperations(BaseOperations):
    def __init__(self, db):
        super().__init__(db)

    def insert_transactions(self, chain: str, transactions: List[Dict[str, Any]], block_number: int) -> bool:
        """
        Bulk insert EVM transactions into the PostgreSQL database.
        Uses execute_values for better performance with partitioned tables.
        """
        try:
            self.db.logger.info(f"Inserting {len(transactions)} {chain} transactions into PostgreSQL database in bulk from block {block_number}.")
            
            execute_values(self.db.cursor, INSERT_EVM_TRANSACTIONS, transactions, page_size=1000)
            self.db.conn.commit()
            self.db.logger.info(f"Successfully inserted {len(transactions)} {chain} transactions into PostgreSQL database from block {block_number}.")
            return True
        except Exception as e:
            self.db.logger.error(f"Error inserting {chain} transactions into PostgreSQL database: {e}")
            self.db.conn.rollback()
            return False
        
    def insert_event(self, chain: str, event_object) -> bool:
        """
        Insert or update an EVM event signature.
        Updates contract_address only if it was previously NULL.
        """
        try:
            query = INSERT_EVM_EVENTS
            self.db.cursor.execute(query,(
                chain,
                event_object.signature_hash,
                event_object.name,
                event_object.full_signature,
                json.dumps(event_object.input_types),
                json.dumps(event_object.indexed_inputs),
                json.dumps(event_object.inputs),
                event_object.contract_address
            ))
            self.db.conn.commit()
            return True
        except Exception as e:
            # Change to debug
            self.db.logger.error(f"Error inserting EVM event for chain {chain}: {e}")
            self.db.conn.rollback()
            return False

    def insert_contract_abi(self, chain: str, contract_address: str, abi: dict) -> bool:
        """
        Insert or update an EVM contract ABI.
        """
        try:
            self.db.cursor.execute(INSERT_EVM_CONTRACT_ABI, (
                chain,
                contract_address,
                json.dumps(abi)
            ))
            self.db.conn.commit()
            return True
        except Exception as e:
            # Change to debug
            self.db.logger.error(f"Error inserting EVM contract ABI for chain {chain}: {e}")
            self.db.conn.rollback()
            return False

    def insert_swap(self, chain: str, swap_info) -> bool:
        """
        Insert or update an EVM swap.
        """
        try:
            self.db.cursor.execute(INSERT_EVM_SWAP, (
                swap_info.address,
                swap_info.factory,
                swap_info.fee,
                swap_info.token0_name,
                swap_info.token1_name,
                swap_info.token0_address,
                swap_info.token1_address,
                swap_info.name,
                chain
            ))
            self.db.conn.commit()
            return True
        except Exception as e:
            self.db.logger.error(f"Error inserting EVM swap for chain {chain}: {e}")
            self.db.conn.rollback()
            return False
        
    def insert_token_info(self, chain: str, token_info) -> bool:
        """
        Insert or update an EVM token info.
        """
        try:
            self.db.cursor.execute(INSERT_EVM_TOKEN_INFO, (
                token_info.address,
                token_info.name,
                token_info.symbol,
                token_info.decimals,
                chain,
            ))
            self.db.conn.commit()
            self.db.logger.info(f"Successfully inserted {token_info.name} info for chain {chain}.")
            return True
        except Exception as e:
            self.db.logger.error(f"Error inserting EVM token info for chain {chain}: {e}")
            self.db.conn.rollback()
            return False

    def contract_to_factory(self, chain: str, contract_address: str, factory_address: str) -> bool:
        """
        Insert an EVM contract to factory mapping into the PostgreSQL database.
        """
        try:
            self.db.cursor.execute(INSERT_EVM_CONTRACT_TO_FACTORY, (
                contract_address,
                factory_address,
                chain
            ))
            self.db.conn.commit()
            self.db.logger.info(f"Successfully inserted EVM contract {contract_address} to factory {factory_address} mapping for chain {chain}.")
            return True
        except Exception as e:
            self.db.logger.error(f"Error inserting EVM contract {contract_address} to factory {factory_address} mapping for chain {chain}: {e}")
            self.db.conn.rollback()
            return False
    
    def insert_transaction_swap(self, chain: str, swap_info, address: str, tx_hash: str, index: int, timestamp: int) -> bool:
        """
        Insert or update an EVM transaction swap.
        """
        try:
            self.db.cursor.execute(INSERT_EVM_TRANSACTION_SWAP, (
                chain,
                address,
                tx_hash,
                index,
                timestamp,
                swap_info.amount0,
                swap_info.amount1,
                swap_info.token0,
                swap_info.token1,
                swap_info.isAmount0In
            ))
            self.db.conn.commit()
            return True
        except Exception as e:
            self.db.logger.error(f"Error inserting EVM transaction swap for chain {chain}: {e}")
            self.db.conn.rollback()
            return False


