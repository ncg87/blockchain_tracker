from web3 import Web3
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from eth_typing import ChecksumAddress
import json

@dataclass
class ProtocolIdentification:
    protocol_name: str
    identification_method: str
    creation_tx: Optional[str] = None
    factory_address: Optional[str] = None
    token0: Optional[str] = None  # For DEX pairs
    token1: Optional[str] = None  # For DEX pairs
    pair_index: Optional[int] = None  # Pair number in factory
    creation_event: Optional[dict] = None  # Full creation event data

class DefinitiveProtocolIdentifier:
    def __init__(self, web3: Web3):
        self.w3 = web3
        
        # Known factory contracts with their deployment blocks for efficiency
        self.FACTORIES = {
            'UniswapV2': {
                'address': '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f',
                'deploy_block': 10000835,
                'creation_code_hash': '0x96e8ac4277198ff8b6f785478aa9a39f403cb768dd02cbee326c3e7da348845f'
            },
            'SushiSwap': {
                'address': '0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac',
                'deploy_block': 10794229,
                'creation_code_hash': '0xe18a34eb0e04b04f7a0ac29a6e80748dca96319b42c54d679cb821dca90c6303'
            },
            # Add more factories with their deployment blocks
        }
        
        # Load factory ABIs
        self.factory_abis = {}
        for protocol in self.FACTORIES:
            try:
                with open(f'abis/{protocol.lower()}_factory.json', 'r') as f:
                    self.factory_abis[protocol] = json.load(f)
            except FileNotFoundError:
                print(f"Warning: ABI file for {protocol} factory not found")

    def get_creation_transaction(self, address: str) -> Optional[dict]:
        """
        Get the creation transaction for a contract by searching historical blocks.
        Returns None if creation transaction cannot be found.
        """
        address = self.w3.to_checksum_address(address)
        
        # Get the earliest known factory deployment block
        earliest_factory_block = min(
            factory['deploy_block'] for factory in self.FACTORIES.values()
        )
        
        # Get current code to verify contract exists
        code = self.w3.eth_get_code(address, 'latest')
        if code == '0x':
            return None
            
        # Binary search for contract creation
        left = earliest_factory_block
        right = self.w3.eth_block_number()
        
        while left <= right:
            mid = (left + right) // 2
            code = self.w3.eth_get_code(address, mid)
            
            if code == '0x':
                left = mid + 1
            else:
                right = mid - 1
        
        creation_block = left
        
        # Get transaction that created the contract
        block = self.w3.eth_get_block(creation_block, full_transactions=True)
        for tx in block['transactions']:
            # Check if this transaction created our contract
            if tx['to'] is None:  # Contract creation transaction
                receipt = self.w3.eth_get_transaction_receipt(tx['hash'])
                if receipt['contract_address'] and \
                   receipt['contract_address'].lower() == address.lower():
                    return tx
                    
        return None

    def identify_from_factory(self, address: str) -> Optional[ProtocolIdentification]:
        """
        Definitively identify a contract by checking if it was created by a known factory
        and extracting detailed creation information from events.
        """
        creation_tx = self.get_creation_transaction(address)
        if not creation_tx:
            return None
            
        creator_address = creation_tx['from']
        
        # Check if creator is a known factory
        for protocol, factory in self.FACTORIES.items():
            if creator_address.lower() == factory['address'].lower():
                # Get the creation event details
                creation_details = self.get_creation_event_details(
                    protocol,
                    creation_tx['hash'].hex(),
                    address
                )
                
                if creation_details:
                    return ProtocolIdentification(
                        protocol_name=protocol,
                        identification_method='factory_creation',
                        creation_tx=creation_tx['hash'].hex(),
                        factory_address=creator_address,
                        token0=creation_details.get('token0'),
                        token1=creation_details.get('token1'),
                        pair_index=creation_details.get('pair_index'),
                        creation_event=creation_details
                    )
                else:
                    # Still return basic identification if event parsing fails
                    return ProtocolIdentification(
                        protocol_name=protocol,
                        identification_method='factory_creation',
                        creation_tx=creation_tx['hash'].hex(),
                        factory_address=creator_address
                    )
        
        return None
        
    def get_creation_event_details(self, protocol: str, tx_hash: str, pair_address: str) -> Optional[dict]:
        """
        Extract detailed information from the contract creation event.
        """
        try:
            # Get transaction receipt for events
            receipt = self.w3.eth_get_transaction_receipt(tx_hash)
            
            # Create contract instance for the factory
            factory_address = self.FACTORIES[protocol]['address']
            factory_abi = self.factory_abis.get(protocol, [])
            factory_contract = self.w3.eth_contract(
                address=factory_address,
                abi=factory_abi
            )
            
            # Look for creation event in the transaction
            # Example for Uniswap V2:
            if protocol == 'UniswapV2':
                pair_created_event = None
                for log in receipt['logs']:
                    if log['address'].lower() == factory_address.lower():
                        try:
                            event = factory_contract.events.PairCreated().process_log(log)
                            if event['args']['pair'].lower() == pair_address.lower():
                                pair_created_event = event
                                break
                        except Exception:
                            continue
                
                if pair_created_event:
                    return {
                        'token0': pair_created_event['args']['token0'],
                        'token1': pair_created_event['args']['token1'],
                        'pair_index': pair_created_event['args'][''].hex(),  # Usually the 4th argument
                        'raw_event': pair_created_event
                    }
            
            # Add similar blocks for other protocols
            elif protocol == 'SushiSwap':
                # SushiSwap uses same event structure as Uniswap V2
                pass
                
        except Exception as e:
            print(f"Error getting creation event details: {e}")
            
        return None

    def verify_creation_code(self, address: str, creation_tx: dict) -> Optional[str]:
        """
        Verify the contract creation code matches known protocol initialization code.
        """
        # Get the creation bytecode from the transaction
        creation_code = creation_tx['input']
        code_hash = self.w3.keccak(hexstr=creation_code).hex()
        
        # Check against known creation code hashes
        for protocol, factory in self.FACTORIES.items():
            if code_hash == factory['creation_code_hash']:
                return protocol
                
        return None

    def identify_protocol(self, address: str) -> Optional[ProtocolIdentification]:
        """
        Main identification method that only returns 100% certain identifications.
        """
        # First try factory-based identification
        factory_id = self.identify_from_factory(address)
        if factory_id:
            return factory_id
            
        # Get creation transaction for further analysis
        creation_tx = self.get_creation_transaction(address)
        if not creation_tx:
            return None
            
        # Verify creation code
        protocol = self.verify_creation_code(address, creation_tx)
        if protocol:
            return ProtocolIdentification(
                protocol_name=protocol,
                identification_method='creation_code',
                creation_tx=creation_tx['hash'].hex()
            )
            
        return None

    def batch_identify(self, addresses: List[str]) -> Dict[str, ProtocolIdentification]:
        """
        Batch identify multiple contracts efficiently.
        """
        results = {}
        for address in addresses:
            result = self.identify_protocol(address)
            if result:
                results[address] = result
        return results

# Example usage:
def main():
    # Initialize Web3 with your provider
    w3 = Web3(Web3.HTTPProvider('YOUR_NODE_URL'))
    
    identifier = DefinitiveProtocolIdentifier(w3)
    
    # Example contract address
    contract = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"  # Uniswap V2 Router
    
    result = identifier.identify_protocol(contract)
    if result:
        print(f"Protocol: {result.protocol_name}")
        print(f"Identification Method: {result.identification_method}")
        print(f"Creation Transaction: {result.creation_tx}")
        print(f"Factory Address: {result.factory_address}")
    else:
        print("Could not definitively identify protocol")

if __name__ == "__main__":
    main()