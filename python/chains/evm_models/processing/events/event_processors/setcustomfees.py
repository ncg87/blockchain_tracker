from .processors import EventProcessor
from operator import itemgetter

get_contract = itemgetter('contract')

class SetCustomFeeProcessor(EventProcessor):
    def __init__(self, db_operator, chain):
        super().__init__(db_operator, chain)
        self.logger.info("SetCustomFeeProcessor initialized")

    def process_event(self, event, signature, tx_hash, index, timestamp):
        address = get_contract(event)

