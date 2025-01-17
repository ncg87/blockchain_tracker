from web3 import Web3
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import json

@dataclass
class ContractType:
    name: str
    description: str
    interfaces: List[str]
    creation_pattern: Optional[str] = None

class DeFiAnalyzer:
    def __init__(self, web3_url: str):
        self.w3 = Web3(Web3.HTTPProvider(web3_url))
        
        # Define known contract types and their identifiers
        self.CONTRACT_TYPES = {
            'DEX_PAIR': ContractType(
                name='Liquidity Pair',
                description='Trading pair for swapping between two tokens',
                interfaces=['token0()', 'token1()', 'getReserves()', 'mint(address)', 'burn(address)'],
                creation_pattern='FACTORY'
            ),
            'DEX_ROUTER': ContractType(
                name='Router',
                description='Router contract for executing trades and managing liquidity',
                interfaces=['swapExactTokensForTokens(uint256,uint256,address[],address,uint256)',
                          'addLiquidity(address,address,uint256,uint256,uint256,uint256,address,uint256)']
            ),
            'LENDING_POOL': ContractType(
                name='Lending Pool',
                description='Pool for depositing and borrowing assets',
                interfaces=['deposit(address,uint256,address,uint16)',
                          'borrow(address,uint256,uint256,uint16,address)']
            ),
            'STAKING_POOL': ContractType(
                name='Staking Pool',
                description='Pool for staking tokens to earn rewards',
                interfaces=['stake(uint256)', 'withdraw(uint256)', 'getReward()']
            ),
            'GOVERNANCE': ContractType(
                name='Governance',
                description='Contract for governance proposals and voting',
                interfaces=['propose(address[],uint256[],string[],bytes[],string)',
                          'castVote(uint256,uint8)']
            )
        }

        # Known protocol factories and their contracts
        self.PROTOCOL_FACTORIES = {
            'UniswapV2': {
                'factory': '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f',
                'router': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
            },
            'SushiSwap': {
                'factory': '0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac',
                'router': '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F',
            }
        }

    def get_contract_interfaces(self, address: str) -> List[str]:
        """Get all function selectors implemented by the contract."""
        code = self.w3.eth.get_code(address)
        
        # Load common interface selectors
        try:
            with open('interfaces/selectors.json', 'r') as f:
                known_selectors = json.load(f)
        except FileNotFoundError:
            # Fallback to basic selectors if file not found
            known_selectors = {
                '0x0902f1ac': 'getReserves()',
                '0x022c0d9f': 'swap(uint256,uint256,address,bytes)',
                '0x89afcb44': 'burn(address)',
                '0x6a627842': 'mint(address)',
                '0x0dfe1681': 'token0()',
                '0xd21220a7': 'token1()'
            }
            
        implemented_selectors = []
        code_hex = code.hex()
        
        # Check which interfaces are implemented
        for selector, signature in known_selectors.items():
            if selector[2:] in code_hex:  # Remove '0x' prefix for comparison
                implemented_selectors.append(signature)
                
        return implemented_selectors

    def identify_contract_type(self, address: str, interfaces: List[str]) -> Optional[ContractType]:
        """Identify contract type based on implemented interfaces."""
        for type_id, contract_type in self.CONTRACT_TYPES.items():
            # Check if contract implements all required interfaces
            if all(iface in interfaces for iface in contract_type.interfaces):
                return contract_type
        return None

    def get_contract_relationships(self, address: str) -> Dict[str, Any]:
        """Identify relationships with other contracts (factory, router, etc)."""
        relationships = {}
        
        # Try to get related contracts through common interfaces
        contract = self.w3.eth.contract(address=address, abi=[
            {"constant": True, "inputs": [], "name": "factory", "outputs": [{"type": "address"}], "type": "function"},
            {"constant": True, "inputs": [], "name": "token0", "outputs": [{"type": "address"}], "type": "function"},
            {"constant": True, "inputs": [], "name": "token1", "outputs": [{"type": "address"}], "type": "function"},
        ])

        # Get related contracts
        try:
            relationships['factory'] = contract.functions.factory().call()
            # Check if factory matches known protocols
            factory_addr = relationships['factory'].lower()
            for protocol, addresses in self.PROTOCOL_FACTORIES.items():
                if addresses['factory'].lower() == factory_addr:
                    relationships['protocol'] = protocol
                    break
        except Exception:
            pass

        try:
            relationships['token0'] = contract.functions.token0().call()
            relationships['token1'] = contract.functions.token1().call()
            
            # Get token symbols
            token_abi = [
                {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"type": "string"}], "type": "function"}
            ]
            
            try:
                token0 = self.w3.eth.contract(address=relationships['token0'], abi=token_abi)
                token1 = self.w3.eth.contract(address=relationships['token1'], abi=token_abi)
                
                relationships['token0_symbol'] = token0.functions.symbol().call()
                relationships['token1_symbol'] = token1.functions.symbol().call()
            except Exception:
                pass
                
        except Exception:
            pass

        return relationships

    def analyze_contract(self, address: str) -> Dict[str, Any]:
        """
        Analyze any DeFi contract and return comprehensive information about its
        purpose, type, and relationships.
        """
        address = self.w3.to_checksum_address(address)
        
        # Get implemented interfaces
        interfaces = self.get_contract_interfaces(address)
        
        # Identify contract type
        contract_type = self.identify_contract_type(address, interfaces)
        
        # Get relationships with other contracts
        relationships = self.get_contract_relationships(address)
        
        # Build analysis result
        analysis = {
            'address': address,
            'type': contract_type.name if contract_type else 'Unknown',
            'description': contract_type.description if contract_type else 'Unknown contract type',
            'relationships': relationships,
            'interfaces': interfaces,
        }
        
        return analysis

def print_analysis(analysis: Dict[str, Any]) -> None:
    """Pretty print the analysis results."""
    print(f"\n🔍 Contract Analysis")
    print(f"==================")
    print(f"📜 Address: {analysis['address']}")
    print(f"📝 Type: {analysis['type']}")
    print(f"📋 Description: {analysis['description']}")
    
    if 'relationships' in analysis:
        print("\n🔗 Relationships:")
        for key, value in analysis['relationships'].items():
            print(f"  {key}: {value}")
    
    if len(analysis['interfaces']) > 0:
        print("\n⚙️ Implemented Interfaces:")
        for interface in analysis['interfaces']:
            print(f"  - {interface}")

# Usage example:
if __name__ == "__main__":
    # Initialize with your node URL
    analyzer = DeFiAnalyzer('YOUR_NODE_URL')
    
    # Example: UniswapV2 USDC/ETH pair
    contract = "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc"
    
    result = analyzer.analyze_contract(contract)
    print_analysis(result)