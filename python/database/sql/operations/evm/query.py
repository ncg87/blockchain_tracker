from ..base import BaseOperations
from typing import List, Dict, Any, Optional
from ...queries import (QUERY_EVM_FACTORY_CONTRACT, QUERY_EVM_TRANSACTIONS, QUERY_ADDRESS_HISTORY, 
                        QUERY_EVM_EVENT, QUERY_EVM_CONTRACT_ABI, QUERY_EVM_SWAP, QUERY_EVM_TOKEN_INFO, 
                        QUERY_EVM_FACTORY_CONTRACT, QUERY_RECENT_EVM_TRANSACTIONS, QUERY_EVM_EVENT_BY_CONTRACT_ADDRESS, 
                        QUERY_EVM_EVENT_BY_CONTRACT_ADDRESS_ALL_NETWORKS, QUERY_ALL_EVM_SWAPS, QUERY_ALL_EVM_SWAPS_BY_NETWORK, 
                        QUERY_EVM_SWAP_ALL_NETWORKS, QUERY_EVM_TOKEN_INFO_ALL_NETWORKS)
from ..models import EventSignature, ContractInfo, TokenInfo
import json


class EVMQueryOperations(BaseOperations):
    def __init__(self, db):
        super().__init__(db)

    def query_transactions(self, network: str, block_number: int) -> List[Dict[str, Any]]:
        """
        Query EVM transactions for a specific block.
        """
        try:
            self.db.cursor.execute(QUERY_EVM_TRANSACTIONS, (
                network, 
                block_number
            ))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying transactions for network {network}: {e}")
            return []
        
    def query_recent_transactions(self, network: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Query recent EVM transactions.
        """
        try:
            self.db.cursor.execute(QUERY_RECENT_EVM_TRANSACTIONS, (
                network,
                limit
            ))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying recent transactions for network {network}: {e}")
            return []
        
    def query_address_history(self, network: str, address: str, start_time: int, end_time: int) -> List[Dict[str, Any]]:
        """
        Query transaction history for an address using covering indexes.
        """
        try:
            self.db.cursor.execute(QUERY_ADDRESS_HISTORY, (
                network, 
                start_time, 
                end_time, 
                address,
                address))
            return self.db.cursor.fetchall()
        except Exception as e:
            self.db.logger.error(f"Error querying address history for network {network}: {e}")
            return []
    
    def query_event(self, network: str, signature_hash: str) -> Optional[Dict[str, Any]]:
        """
        Query an EVM event by its network and signature hash.
        """
        try:
            self.db.cursor.execute(QUERY_EVM_EVENT, (
                network, 
                signature_hash
            ))
            result = self.db.cursor.fetchone()
            if result:
                return EventSignature(
                    signature_hash=result.get('signature_hash'),
                    name=result.get('name'),
                    full_signature=result.get('full_signature'),
                    input_types=json.loads(result.get('input_types')),
                    indexed_inputs=json.loads(result.get('indexed_inputs')),
                    inputs=json.loads(result.get('inputs')),
                    contract_address=result.get('contract_address')
                )
            return None
        except Exception as e:
            self.db.logger.error(f"Error querying EVM event for network {network}: {e}")
            return None
        
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
        
    def query_swap(self, network: str, contract_address: str) -> Optional[Dict[str, Any]]:
        """
        Query an EVM swap by its network and address.
        """
        # Change query to * rather than specific columns
        try:
            self.db.cursor.execute(QUERY_EVM_SWAP, (
                network,
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
                    token0_address=result.get('token0_address', None),
                    token1_address=result.get('token1_address', None),
                    name=result.get('name', None)
                )
            return None
        except Exception as e:
            self.db.logger.error(f"Error querying EVM swap for network {network}: {e}")
            return None
    
    def query_swap_all_networks(self, contract_address: str) -> Optional[Dict[str, Any]]:
        """
        Query an EVM swap by its contract address across all networks.
        """
        try:
            self.db.cursor.execute(QUERY_EVM_SWAP_ALL_NETWORKS, (
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
        
    def query_token_info(self, network: str, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Query an EVM token info by its network and address.
        """
        try:
            self.db.cursor.execute(QUERY_EVM_TOKEN_INFO, (
                network,
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
            self.db.logger.error(f"Error querying EVM token info for network {network}: {e}")
            return None

    def query_token_info_all_networks(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Query an EVM token info by its address across all networks.
        """
        try:
            self.db.cursor.execute(QUERY_EVM_TOKEN_INFO_ALL_NETWORKS, (token_address,))
            return self.db.cursor.fetchone()
        except Exception as e:
            self.db.logger.error(f"Error querying EVM token info for address {token_address}: {e}")
            return None
    
    def query_factory_contract(self, network: str, contract_address: str) -> Optional[Dict[str, Any]]:
        """
        Query an EVM factory contract by its network and address.
        """
        try:
            self.db.cursor.execute(QUERY_EVM_FACTORY_CONTRACT, (
                network,
                contract_address
            ))
            return self.db.cursor.fetchone()
        except Exception as e:
            self.db.logger.error(f"Error querying EVM factory contract for network {network}: {e}")
            return None

    def query_event_by_contract_address(self, network: str, contract_address: str) -> List[Dict[str, Any]]:
        """
        Query EVM events by network and contract address.
        Returns a list of events associated with the contract address on the specified network.
        """
        try:
            self.db.cursor.execute(QUERY_EVM_EVENT_BY_CONTRACT_ADDRESS, (
                network,
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
            self.db.logger.error(f"Error querying EVM events by contract address for network {network}: {e}")
            return []

    def query_event_by_contract_address_all_networks(self, contract_address: str) -> List[Dict[str, Any]]:
        """
        Query EVM events by contract address across all networks.
        Returns a list of events associated with the contract address regardless of network.
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
    
    def query_all_evm_swaps_by_network(self, network: str) -> List[Dict[str, Any]]:
        """
        Query all EVM swaps by network.
        """
        try:
            self.db.cursor.execute(QUERY_ALL_EVM_SWAPS_BY_NETWORK, (network,))
            results = self.db.cursor.fetchall()
            return results
        except Exception as e:
            self.db.logger.error(f"Error querying all EVM swaps by network {network}: {e}")
            return []
        
    def query_all_evm_swaps(self) -> List[Dict[str, Any]]:
        """
        Query all EVM swaps.
        """
        try:
            self.db.cursor.execute(QUERY_ALL_EVM_SWAPS)
            results = self.db.cursor.fetchall()
            return results
        except Exception as e:
            self.db.logger.error(f"Error querying all EVM swaps: {e}")
            return []
