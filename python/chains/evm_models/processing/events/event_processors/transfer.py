from typing import Dict, List, Optional
from web3 import Web3
from ..processors import EventProcessor
from ..models import Transfer

class TransferEventProcessor(EventProcessor):
    def get_parameter_mapping(self) -> Dict[str, List[str]]:
        return {
            'from': ['from', 'sender', 'src', 'source', 'fromAddress'],
            'to': ['to', 'recipient', 'dst', 'destination', 'toAddress'],
            'value': ['value', 'amount', 'tokens', 'wad']
        }

    def process(self, event: Dict, network: str) -> Optional[Transfer]:
        try:
            contract_address = Web3.to_checksum_address(event['contract'])
            if self.sql_query_ops:
                coin = self.sql_query_ops.query_evm_token_info(network, contract_address)
                if not coin:
                    return None
            else:
                return None

            return Transfer(
                network=network,
                contract_address=contract_address,
                coin=coin.name,
                coin_address=coin.address,
                coin_symbol=coin.symbol,
                amount=self.get_parameter_value(event['parameters'], 'value'),
                from_address=self.get_parameter_value(event['parameters'], 'from'),
                to_address=self.get_parameter_value(event['parameters'], 'to')
            )
        except Exception as e:
            print(f"Error processing Transfer event: {e}")
            return None