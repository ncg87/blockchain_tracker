from typing import Dict, List, Set
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class ContractMetadata:
    address: str
    name: str = ""
    category: str = ""
    event_types: Set[str] = None
    interaction_count: int = 0
    
    def __post_init__(self):
        if self.event_types is None:
            self.event_types = set()

class ContractAnalyzer:
    # Known contract categories and their typical events
    DEX_EVENTS = {
        'Swap', 'Sync', 'Mint', 'Burn',
        'IncreaseLiquidity', 'DecreaseLiquidity'
    }
    
    LENDING_EVENTS = {
        'Borrow', 'Repay', 'Deposit', 'Withdraw',
        'LiquidationCall', 'Accrue'
    }
    
    NFT_EVENTS = {
        'Transfer', 'Approval', 'ApprovalForAll',
        'Mint', 'Burn', 'Sale'
    }
    
    BRIDGE_EVENTS = {
        'Deposit', 'Withdrawal', 'TokensBridged',
        'Transfer', 'Route'
    }

    def __init__(self):
        self.contracts = {}  # address -> ContractMetadata
        self.contract_interactions = defaultdict(set)  # address -> set of interacting addresses
        
    def process_transaction_events(self, events: List[Dict]) -> None:
        """Process events from a single transaction"""
        if not events:
            return
            
        # Track contracts involved in this transaction
        tx_contracts = set()
        
        for event in events:
            contract_addr = event.get('contract', '').lower()
            if not contract_addr:
                continue
                
            # Create or update contract metadata
            if contract_addr not in self.contracts:
                self.contracts[contract_addr] = ContractMetadata(address=contract_addr)
                
            contract = self.contracts[contract_addr]
            contract.event_types.add(event.get('event', ''))
            contract.interaction_count += 1
            
            tx_contracts.add(contract_addr)
        
        # Update contract interactions
        for addr1 in tx_contracts:
            for addr2 in tx_contracts:
                if addr1 != addr2:
                    self.contract_interactions[addr1].add(addr2)

    def categorize_contract(self, contract: ContractMetadata) -> str:
        """Determine the likely category of a contract based on its events"""
        events = contract.event_types
        
        # Calculate overlap with known event types
        dex_overlap = len(events & self.DEX_EVENTS)
        lending_overlap = len(events & self.LENDING_EVENTS)
        nft_overlap = len(events & self.NFT_EVENTS)
        bridge_overlap = len(events & self.BRIDGE_EVENTS)
        
        # Determine category based on highest overlap
        max_overlap = max(dex_overlap, lending_overlap, nft_overlap, bridge_overlap)
        
        if max_overlap == 0:
            return "Unknown"
        elif max_overlap == dex_overlap:
            return "DEX"
        elif max_overlap == lending_overlap:
            return "Lending"
        elif max_overlap == nft_overlap:
            return "NFT"
        elif max_overlap == bridge_overlap:
            return "Bridge"
            
        return "Unknown"

    def get_contract_analysis(self) -> Dict:
        """Get comprehensive analysis of contract interactions"""
        results = {
            'contract_categories': defaultdict(int),
            'most_active_contracts': [],
            'contract_details': {},
            'interesting_patterns': []
        }
        
        # Analyze each contract
        for addr, contract in self.contracts.items():
            category = self.categorize_contract(contract)
            contract.category = category
            results['contract_categories'][category] += 1
            
            # Store detailed contract info
            results['contract_details'][addr] = {
                'category': category,
                'interaction_count': contract.interaction_count,
                'event_types': list(contract.event_types),
                'interacts_with': list(self.contract_interactions[addr])
            }
        
        # Find most active contracts
        most_active = sorted(
            self.contracts.values(),
            key=lambda x: x.interaction_count,
            reverse=True
        )[:10]
        
        results['most_active_contracts'] = [
            {
                'address': c.address,
                'category': c.category,
                'interaction_count': c.interaction_count,
                'event_types': list(c.event_types)
            }
            for c in most_active
        ]
        
        # Identify interesting patterns
        results['interesting_patterns'] = self._find_interesting_patterns()
        
        return results

    def _find_interesting_patterns(self) -> List[Dict]:
        """Identify interesting patterns in contract interactions"""
        patterns = []
        
        # Find contracts that frequently interact together
        for addr, interactions in self.contract_interactions.items():
            if len(interactions) > 1:  # If contract interacts with multiple others
                contract = self.contracts[addr]
                related_contracts = [self.contracts[x] for x in interactions]
                
                patterns.append({
                    'type': 'multi_contract_interaction',
                    'main_contract': {
                        'address': addr,
                        'category': contract.category,
                        'event_types': list(contract.event_types)
                    },
                    'related_contracts': [
                        {
                            'address': c.address,
                            'category': c.category,
                            'event_types': list(c.event_types)
                        }
                        for c in related_contracts
                    ]
                })
        
        return patterns[:10]  # Return top 10 interesting patterns
