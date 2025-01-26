from ..evm_models import EVMDecoder

class ArbitrumDecoder(EVMDecoder):
    def __init__(self, sql_database):
        super().__init__(sql_database, "Arbitrum") 