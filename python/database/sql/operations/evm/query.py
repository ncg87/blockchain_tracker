from ..base import BaseOperations
from typing import List, Dict, Any, Optional
from ...queries import (QUERY_EVM_FACTORY_CONTRACT, QUERY_EVM_TRANSACTIONS, QUERY_ADDRESS_HISTORY, 
                        QUERY_EVM_EVENT, QUERY_EVM_CONTRACT_ABI, QUERY_EVM_SWAP_INFO, QUERY_EVM_TOKEN_INFO_BY_CHAIN, 
                        QUERY_EVM_FACTORY_CONTRACT, QUERY_RECENT_EVM_TRANSACTIONS, QUERY_EVM_EVENT_BY_CONTRACT_ADDRESS, 
                        QUERY_EVM_EVENT_BY_CONTRACT_ADDRESS_ALL_NETWORKS, QUERY_ALL_EVM_SWAP_INFO, QUERY_ALL_EVM_SWAP_INFO_BY_CHAIN, 
                        QUERY_EVM_SWAP_INFO_BY_CHAIN, QUERY_EVM_TOKEN_INFO, QUERY_EVM_EVENT_BY_CHAIN)
from ..models import EventSignature, ContractInfo, TokenInfo
import json


class EVMQueryOperations(BaseOperations):
    def __init__(self, db):
        super().__init__(db)

    def query_transactions(self, chain: str, block_number: int) -> List[Dict[str, Any]]:
        """
        Query EVM transactions for a specific block.
        """
        try:
            self.db.cursor.execute(QUERY_EVM_TRANSACTIONS, (
                chain, 
                block_number
            ))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying transactions for chain {chain}: {e}")
            return []
        
    def query_recent_transactions(self, chain: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Query recent EVM transactions.
        """
        try:
            self.db.cursor.execute(QUERY_RECENT_EVM_TRANSACTIONS, (
                chain,
                limit
            ))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying recent transactions for chain {chain}: {e}")
            return []
        
    def query_address_history(self, chain: str, address: str, start_time: int, end_time: int) -> List[Dict[str, Any]]:
        """
        Query transaction history for an address using covering indexes.
        """
        try:
            self.db.cursor.execute(QUERY_ADDRESS_HISTORY, (
                chain, 
                start_time, 
                end_time, 
                address,
                address))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying address history for chain {chain}: {e}")
            return []
    
    def event_by_chain(self, chain: str, signature_hash: str) -> Optional[EventSignature]:
        """
        Query an EVM event by its network and signature hash.
        """
        try:

            self.db.cursor.execute(QUERY_EVM_EVENT_BY_CHAIN, (
                chain, 
                signature_hash
            ))
            result = self.db.cursor.fetchone()
            if result:
                return EventSignature(
                    signature_hash=result.get('signature_hash'),
                    event_name=result.get('event_name'),
                    decoded_signature=result.get('decoded_signature'),
                    input_types=json.loads(result.get('input_types')),
                    indexed_inputs=json.loads(result.get('indexed_inputs')),
                    input_names=json.loads(result.get('input_names')),
                    inputs=json.loads(result.get('inputs')),
                )
            return None
        except Exception as e:
            self.db.logger.error(f"Error querying EVM event for chain {chain}: {e}")
            return None
        
    def event(self, signature_hash: str) -> Optional[EventSignature]:
        """
        Query all EVM events for a chain.
        """
        try:

            self.db.cursor.execute(QUERY_EVM_EVENT, (signature_hash,))
            result = self.db.cursor.fetchone()
            if result:
                return EventSignature(
                    signature_hash=result.get('signature_hash'),
                    event_name=result.get('event_name'),
                    decoded_signature=result.get('decoded_signature'),
                    input_types=json.loads(result.get('input_types')),
                    indexed_inputs=json.loads(result.get('indexed_inputs')),
                    input_names=json.loads(result.get('input_names')),
                    inputs=json.loads(result.get('inputs')),
                )
            return None
        except Exception as e:
            self.db.logger.error(f"Error querying EVM event for signature hash {signature_hash}: {e}")
            return []
    def query_contract_abi(self, chain: str, contract_address: str) -> Optional[Dict[str, Any]]:
        """

        Query an EVM contract ABI by its network and address.
        """
        try:
            self.db.cursor.execute(QUERY_EVM_CONTRACT_ABI, (
                chain,
                contract_address
            ))
            return self.db.cursor.fetchone()
        except Exception as e:
            # Make debug
            self.db.logger.error(f"Error querying EVM contract ABI for network {chain}: {e}")
            return  
        
    def swap_info_by_chain(self, chain: str, contract_address: str) -> Optional[Dict[str, Any]]:
        """
        Query an EVM swap by its network and address.
        """
        # Change query to * rather than specific columns
        try:
            self.db.cursor.execute(QUERY_EVM_SWAP_INFO_BY_CHAIN, (
                chain,
                contract_address
            ))
            result = self.db.cursor.fetchone()
            if result:
                return ContractInfo(
                    address=result.get('contract_address'),
                    factory=result.get('factory_address'),
                    fee=result.get('fee', None),
                    token0_name=result.get('token0_name', None),
                    token1_name=result.get('token1_name', None),
                    token0_symbol=result.get('token0_symbol', None),
                    token1_symbol=result.get('token1_symbol', None),
                    token0_decimals=result.get('token0_decimals', None),
                    token1_decimals=result.get('token1_decimals', None),
                    token0_address=result.get('token0_address', None),
                    token1_address=result.get('token1_address', None),
                    name=result.get('name', None)
                )
            return None
        except Exception as e:
            self.db.logger.error(f"Error querying EVM swap for chain {chain}: {e}")
            return None
    
    def swap_info(self, contract_address: str) -> Optional[Dict[str, Any]]:
        """
        Query an EVM swap by its contract address across all chains.
        """
        try:
            self.db.cursor.execute(QUERY_EVM_SWAP_INFO, (
                contract_address,
            ))
            result =  self.db.cursor.fetchone()
            if result:
                return ContractInfo(
                    address=result.get('contract_address'),
                    factory=result.get('factory_address'),
                    fee=result.get('fee', None),
                    token0_name=result.get('token0_name', None),
                    token1_name=result.get('token1_name', None),
                    token0_address=result.get('token0_address', None),
                    token1_address=result.get('token1_address', None),
                    name=result.get('name', None)
                )
            return None
        except Exception as e:
            self.db.logger.error(f"Error querying EVM swap for contract address {contract_address}: {e}")
            return None
        
    def token_info_by_chain(self, chain: str, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Query an EVM token info by its network and address.
        """
        try:
            self.db.cursor.execute(QUERY_EVM_TOKEN_INFO_BY_CHAIN, (
                chain,
                token_address
            ))
            result = self.db.cursor.fetchone()
            if result:
                return TokenInfo(
                    address=result.get('contract_address'),
                    name=result.get('name'),
                    symbol=result.get('symbol'),
                    decimals=result.get('decimals')
                )
            return None
        except Exception as e:
            self.db.logger.error(f"Error querying EVM token info for chain {chain}: {e}")
            return None

    def query_token_info(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Query an EVM token info by its address across all networks.
        """
        try:
            self.db.cursor.execute(QUERY_EVM_TOKEN_INFO, (token_address,))
            result = self.db.cursor.fetchone()
            if result:
                return TokenInfo(
                    address=result.get('contract_address'),
                    name=result.get('name'),
                    symbol=result.get('symbol'),
                    decimals=result.get('decimals')
                )
            return None
        except Exception as e:
            self.db.logger.error(f"Error querying EVM token info for address {token_address}: {e}")
            return None
    
    def factory_contract(self, chain: str, contract_address: str) -> Optional[Dict[str, Any]]:
        """
        Query an EVM factory contract by its chain and address.
        """
        try:
            self.db.cursor.execute(QUERY_EVM_FACTORY_CONTRACT, (
                chain,
                contract_address
            ))
            return self.db.cursor.fetchone()
        except Exception as e:
            self.db.logger.error(f"Error querying EVM factory contract for chain {chain}: {e}")
            return None

    def query_event_by_contract_address(self, chain: str, contract_address: str) -> List[Dict[str, Any]]:
        """
        Query EVM events by chain and contract address.
        Returns a list of events associated with the contract address on the specified chain.
        """
        try:
            self.db.cursor.execute(QUERY_EVM_EVENT_BY_CONTRACT_ADDRESS, (
                chain,
                contract_address
            ))
            results = self.db.cursor.fetchall()
            return [EventSignature(
                signature_hash=result.get('signature_hash'),
                name=result.get('name'),
                full_signature=result.get('full_signature'),
                input_types=json.loads(result.get('input_types')),
                indexed_inputs=json.loads(result.get('indexed_inputs')),
                inputs=json.loads(result.get('inputs')),
                contract_address=result.get('contract_address')
            ) for result in results] if results else []
        except Exception as e:
            self.db.logger.error(f"Error querying EVM events by contract address for chain {chain}: {e}")
            return []

    def query_event_by_contract_address_all_networks(self, contract_address: str) -> List[Dict[str, Any]]:
        """
        Query EVM events by contract address across all chains.
        Returns a list of events associated with the contract address regardless of chain.
        """
        try:
            self.db.cursor.execute(QUERY_EVM_EVENT_BY_CONTRACT_ADDRESS_ALL_NETWORKS, (contract_address,))
            results = self.db.cursor.fetchall()
            return [EventSignature(
                signature_hash=result.get('signature_hash'),
                name=result.get('name'),
                full_signature=result.get('full_signature'),
                input_types=json.loads(result.get('input_types')),
                indexed_inputs=json.loads(result.get('indexed_inputs')),
                inputs=json.loads(result.get('inputs')),
                contract_address=result.get('contract_address')
            ) for result in results] if results else []
        except Exception as e:
            self.db.logger.error(f"Error querying EVM events by contract address across all networks: {e}")
            return []
    
    def all_evm_swap_info_by_chain(self, chain: str) -> List[Dict[str, Any]]:
        """
        Query all EVM swaps by chain.
        """
        try:

            self.db.cursor.execute(QUERY_ALL_EVM_SWAP_INFO_BY_CHAIN, (chain,))
            results = self.db.cursor.fetchall()
            return results
        except Exception as e:
            self.db.logger.error(f"Error querying all EVM swaps by chain {chain}: {e}")
            return []
        
    def all_evm_swap_info(self) -> List[Dict[str, Any]]:
        """
        Query all EVM swaps.
        """
        try:
            self.db.cursor.execute(QUERY_ALL_EVM_SWAP_INFO)
            results = self.db.cursor.fetchall()
            return results
        except Exception as e:
            self.db.logger.error(f"Error querying all EVM swaps: {e}")
            return []
