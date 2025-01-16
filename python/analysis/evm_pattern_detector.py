from dataclasses import dataclass, field
from typing import List, Dict, Set
from collections import defaultdict
import json
from .utils import ContractAnalyzer

@dataclass
class Pattern:
    event_sequence: List[tuple] = field(default_factory=list)  # List of (contract, event) pairs
    transaction_hashes: Set[str] = field(default_factory=set)
    frequency: int = 0

class PatternDetector:
    def __init__(self):
        self.patterns = defaultdict(Pattern)
        self.contract_analyzer = ContractAnalyzer()

    def create_pattern_key(self, events: List[dict]) -> str:
        """Create a key from sequence of (contract, event) pairs"""
        pattern = [
            (event.get('contract', '').lower(), event.get('event', ''))
            for event in events
        ]
        return json.dumps(pattern)

    def process_transaction(self, transaction: dict) -> None:
        """Process a single transaction"""
        events = transaction.get('log_data', [])
        if not events:
            return

        pattern_key = self.create_pattern_key(events)
        pattern = self.patterns[pattern_key]
        
        # Update pattern data
        if not pattern.event_sequence:
            pattern.event_sequence = [
                (event.get('contract', '').lower(), event.get('event', ''))
                for event in events
            ]
        
        pattern.transaction_hashes.add(transaction['transaction_hash'])
        pattern.frequency += 1

        # Analyze contract interactions
        self.contract_analyzer.process_transaction_events(events)

    def get_patterns(self, min_frequency: int = 2) -> List[Dict]:
        """Get all patterns that appear at least min_frequency times"""
        results = []
        
        for pattern in self.patterns.values():
            if pattern.frequency < min_frequency:
                continue
                
            results.append({
                'sequence': pattern.event_sequence,
                'frequency': pattern.frequency,
                'sample_tx': list(pattern.transaction_hashes)[:5]
            })
            
        return sorted(results, key=lambda x: x['frequency'], reverse=True)

    def get_analysis(self, min_frequency: int = 2) -> Dict:
        """Get comprehensive analysis including patterns and contract insights"""
        pattern_results = self.get_patterns(min_frequency)
        contract_analysis = self.contract_analyzer.get_contract_analysis()
        
        return {
            'patterns': pattern_results,
            'contract_analysis': contract_analysis
        }

# Example usage:
def analyze_patterns(transactions: List[dict], min_frequency: int = 2) -> Dict:
    detector = PatternDetector()
    
    for tx in transactions:
        detector.process_transaction(tx)
    
    patterns = detector.get_patterns(min_frequency)
    
    return {
        'total_transactions': len(transactions),
        'unique_patterns': len(patterns),
        'patterns': patterns
    }