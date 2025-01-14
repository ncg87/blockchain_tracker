from ..evm_models import EVMDecoder

class BNBDecoder(EVMDecoder):
    def __init__(self, sql_database):
        super().__init__(sql_database, "BNB")