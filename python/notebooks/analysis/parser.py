from dataclasses import dataclass
from typing import Dict, List, Tuple, Any, Optional
from web3 import Web3

@dataclass
class Transfer:
    coin: str
    coin_address: str
    coin_symbol: str
    amount: float
    from_address: str
    to_address: str
    contract_address: str

@dataclass
class Sync:
    token0: str
    token1: str
    amount0: float
    amount1: float

@dataclass
class Swap:
    from_token: str
    from_amount: float
    from_address: str
    to_token: str
    to_amount: float
    to_address: str

class TransactionParser:
    def __init__(self, sql_query_ops, sql_insert_ops, processor):
        """
        Initialize the TransactionParser with necessary database operations.
        
        Args:
            sql_query_ops: SQL query operations instance
            sql_insert_ops: SQL insert operations instance
            processor: Blockchain processor instance
        """
        self.sql_query_ops = sql_query_ops
        self.sql_insert_ops = sql_insert_ops
        self.processor = processor
        self.network = 'Ethereum'

    def get_parameter_value(self, parameters: dict, parameter_type: str) -> str:
        """
        Get parameter value by checking multiple possible key variations.
        
        Args:
            parameters: Dict containing event parameters
            parameter_type: Either 'to' or 'from' to indicate which type of address to look for
        
        Returns:
            str: The found address value
            
        Raises:
            KeyError: If no matching parameter is found
        """
        if parameter_type == 'to':
            possible_keys = ['to', 'recipient', 'dst', 'destination', 'toAddress']
        else:  # from
            possible_keys = ['from', 'sender', 'src', 'source', 'fromAddress']
            
        for key in possible_keys:
            if key in parameters:
                return parameters[key]['value']
                
        raise KeyError(f"No matching {parameter_type} parameter found in: {list(parameters.keys())}")

    def process_transfer(self, event: Dict) -> Optional[Transfer]:
        """
        Process a Transfer event and return a Transfer object.
        
        Args:
            event: The event data dictionary

        Returns:
            Transfer object if successful, None if processing fails
        """
        try:
            contract_address = Web3.to_checksum_address(event['contract'])
            coin = self.sql_query_ops.query_evm_token_info(self.network, contract_address)
            if coin is None:
                coin = self.processor._process_coin(event['contract'])
                coin = self.sql_query_ops.query_evm_token_info(self.network, contract_address)
                
            return Transfer(
                coin=coin.name,
                coin_address=coin.address,
                coin_symbol=coin.symbol,
                amount=event['parameters']['value']['value'],
                from_address=self.get_parameter_value(event['parameters'], 'from'),
                to_address=self.get_parameter_value(event['parameters'], 'to'),
                contract_address=event['contract']
            )
        except Exception as e:
            return e

    def process_swap(self, event: Dict) -> Optional[Swap]:
        """
        Process a Swap event and return a Swap object.
        
        Args:
            event: The event data dictionary
            
        Returns:
            Swap object if successful, None if processing fails
        """
        try:
            contract_address = Web3.to_checksum_address(event['contract'])
            swap = self.sql_query_ops.query_evm_swap(self.network, contract_address)
            if swap is None:
                swap = self.processor._process_swaps(contract_address)
                
            token0 = swap.token0_name
            token1 = swap.token1_name
            from_address = self.get_parameter_value(event['parameters'], 'from')
            to_address = self.get_parameter_value(event['parameters'], 'to')
            
            if event['parameters']['amount0In']['value'] == 0:
                from_amount = event['parameters']['amount1In']['value']
                to_amount = event['parameters']['amount0Out']['value']
                from_token = token1
                to_token = token0
            else:
                from_amount = event['parameters']['amount0In']['value']
                to_amount = event['parameters']['amount1Out']['value']
                from_token = token0
                to_token = token1
                
            return Swap(
                from_token=from_token,
                from_amount=from_amount,
                from_address=from_address,
                to_token=to_token,
                to_amount=to_amount,
                to_address=to_address
            )
        except Exception as e:
            return None

    def parse_transactions(self, query: List[Dict]) -> Tuple[Dict, List]:
        """
        Parse transaction events and return parsed transactions and any bad events.
        
        Args:
            query: List of transaction data
            
        Returns:
            Tuple containing:
                - Dictionary of parsed transactions
                - List of bad events that couldn't be processed
        """
        parsed_transactions = {}
        bad_events = []

        for item in query:
            parsed_transactions[item['transaction_hash']] = []
            for event in item['log_data']:
                if event['event'] == 'Transfer':
                    result = self.process_transfer(event, self.network)
                    if result:
                        parsed_transactions[item['transaction_hash']].append(result)
                    else:
                        bad_events.append(['Transfer', event])
                        
                elif event['event'] == 'Swap':
                    result = self.process_swap(event, self.network)
                    if result:
                        parsed_transactions[item['transaction_hash']].append(result)
                    else:
                        bad_events.append(['Swap', event])
                
        return parsed_transactions, bad_events