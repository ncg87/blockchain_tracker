from ..models import ArbitarySync, TokenSync
from typing import Optional, Dict
from operator import itemgetter
from .processors import EventProcessor
from datetime import datetime, timedelta


get_to = itemgetter('to')
get_sender = itemgetter('sender')
get_recipient = itemgetter('recipient')
get_reserve0 = itemgetter('reserve0')
get_reserve1 = itemgetter('reserve1')
get_value = itemgetter('value')
get_contract = itemgetter('contract')
get_log_index = itemgetter('log_index')
get_vReserve0 = itemgetter('vReserve0')
get_vReserve1 = itemgetter('vReserve1')
get_fictiveReserve0 = itemgetter('fictiveReserve0')
get_fictiveReserve1 = itemgetter('fictiveReserve1')
get_priceAverage0 = itemgetter('priceAverage0')
get_priceAverage1 = itemgetter('priceAverage1')
get_parameters = itemgetter('parameters')
get_value = itemgetter('value')


class SyncProcessor(EventProcessor):
    def __init__(self, db_operator, chain):
        super().__init__(db_operator, chain)
        self.logger.info("SyncProcessor initialized")
        # Define special signatures we want to track
        self.special_signatures = {
            # Add sync-specific signatures here
        }

    def process_event(self, event: dict, signature: str, tx_hash: str, index: int, timestamp: int):
        try:
            # Track special signatures before processing
            if signature in self.special_signatures:
                contract_address = get_contract(event)
                self.increment_known_protocol(signature, contract_address)
            
            protocol_info = self.protocol_map[signature]
            
            parameters = get_parameters(event)
            sync_info = protocol_info(parameters)
            
            address = get_contract(event)
            log_index = get_log_index(event)
            
            contract_info = self.db_operator.sql.query.evm.swap_info_by_chain(self.chain, address)
            
            if contract_info is None:
                return None
            
            if isinstance(sync_info, ArbitarySync):
                sync_info = TokenSync.from_sync_info(sync_info, contract_info)
            
            self.db_operator.sql.insert.evm.sync(self.chain, sync_info, address, tx_hash, log_index, timestamp)
            
            return sync_info

        except KeyError:


            self.increment_unknown_protocol(signature)
            self.logger.error(f"Unknown protocol: {signature}")
            return None
        except Exception as e:
            self.logger.error(f"Error processing event for {self.chain} - {e}", exc_info=True)
            return None

    def create_protocol_map(self):
        return {
            "1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1" : self.reserve0_reserve1,
            "2a368c7f33bb86e2d999940a3989d849031aff29b750f67947e6b8e8c3d2ffd6" : self.reserve0_reserve1_fictiveReserve0_fictiveReserve1_priceAverage0_priceAverage1,
            "2f9d55abfefdfd4c3a83e00a1b419b3c2fe4b83100c559f0e2213e57f6e0bba9" : self.vReserve0_vReserve1_reserve0_reserve1,
            "cf2aa50876cdfbb541206f89af0ee78d44a2abf8d328e37fa4917f982149848a" : self.reserve0_reserve1,
            
        }
    
    def reserve0_reserve1(self, parameters):
        reserve0 = get_value(get_reserve0(parameters))
        reserve1 = get_value(get_reserve1(parameters))
        return ArbitarySync(
            reserve0 = reserve0,
            reserve1 = reserve1
        )

        

    def reserve0_reserve1_fictiveReserve0_fictiveReserve1_priceAverage0_priceAverage1(self, parameters):
        reserve0 = get_value(get_reserve0(parameters))
        reserve1 = get_value(get_reserve1(parameters))
        fictiveReserve0 = get_value(get_fictiveReserve0(parameters))
        fictiveReserve1 = get_value(get_fictiveReserve1(parameters))
        priceAverage0 = get_value(get_priceAverage0(parameters))
        priceAverage1 = get_value(get_priceAverage1(parameters))

        return ArbitarySync(
            reserve0 = fictiveReserve0,
            reserve1 = fictiveReserve1,
        )
        





    def vReserve0_vReserve1_reserve0_reserve1(self, parameters):

        reserve0 = get_value(get_reserve0(parameters))
        reserve1 = get_value(get_reserve1(parameters))
        vReserve0 = get_value(get_vReserve0(parameters))
        vReserve1 = get_value(get_vReserve1(parameters))
        return ArbitarySync(
            reserve0 = vReserve0,
            reserve1 = vReserve1
        )





    def get_unknown_protocol_counts(self) -> Dict[str, int]:

        return self.get_unknown_protocols()

    def get_known_protocol_key(self, signature: str) -> str:
        """Generate a cache key for known protocols"""
        return f"known_protocols:{signature}"

    def increment_known_protocol(self, signature: str, contract_address: str) -> int:
        """Increment counter for specific contract address under a signature with 24h TTL"""
        cache_key = self.get_known_protocol_key(signature)
        pipe = self.redis_client.pipeline()
        
        # Increment the counter for this specific contract
        pipe.hincrby(cache_key, contract_address, 1)
        pipe.expire(cache_key, timedelta(days=1))
        
        result = pipe.execute()
        return result[0]  # Return new counter value
