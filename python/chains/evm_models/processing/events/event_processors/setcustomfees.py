from .processors import EventProcessor
from operator import itemgetter
from ..models import CustomFee

get_contract = itemgetter('contract')
get_parameters = itemgetter('parameters')
get_value = itemgetter('value')
get_pool = itemgetter('pool')
get_fee = itemgetter('fee')
get_log_index = itemgetter('log_index')

class SetCustomFeeProcessor(EventProcessor):
    def __init__(self, db_operator, chain):
        super().__init__(db_operator, chain)
        self.logger.info("SetCustomFeeProcessor initialized")

    def process_event(self, event, signature, tx_hash, index, timestamp):
        try:
            # Track special signatures if needed
            if signature in self.special_signatures:
                contract_address = get_contract(event)
                self.increment_known_protocol(signature, contract_address)
            
            # Get the event parameters
            parameters = get_parameters(event)
            log_index = get_log_index(event)
            
            # Get the pool address and fee value from the parameters
            pool_address = get_value(get_pool(parameters))
            fee_value = get_value(get_fee(parameters))
            
            # Create a CustomFee object
            custom_fee = CustomFee(
                pool=pool_address,
                fee=fee_value
            )
            
            # Insert the custom fee event into the database if needed
            #self.db_operator.sql.insert.evm.custom_fee(
            #    self.chain, 
            #    custom_fee, 
            #    tx_hash, 
            #    log_index, 
            #    timestamp
            #)
            
            return custom_fee
            
        except KeyError:
            # Handle unknown protocol
            self.increment_unknown_protocol(signature)
            self.logger.error(f"Unknown protocol: {signature}")
            return None
        except Exception as e:
            self.logger.error(f"Error processing SetCustomFee event: {e}", exc_info=True)
            return None

    def create_protocol_map(self):
        # Map the signature to the appropriate processing function
        # The SetCustomFee event signature is: SetCustomFee(address,uint256)
        # Keccak hash: 0xae468ce586f9a87660fdffc1448cee942042c16ae2f02046b134b5224f31936b
        return {
            "0xae468ce586f9a87660fdffc1448cee942042c16ae2f02046b134b5224f31936b": self.pool_fee
        }
    
    def pool_fee(self, parameters):
        """Process a pool fee event"""
        pool = get_value(get_pool(parameters))
        fee = get_value(get_fee(parameters))
        
        return {
            "pool": pool,
            "fee": fee
        }

