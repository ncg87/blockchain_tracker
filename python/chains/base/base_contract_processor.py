from ..evm_models import EVMContractProcessor

class BaseContractProcessor(EVMContractProcessor):
    def __init__(self, db):
        super().__init__(db, "Base")
        self.db = db
