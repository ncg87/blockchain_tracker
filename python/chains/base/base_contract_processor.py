from ..evm_models import EVMContractProcessor
from config import Settings
class BaseContractProcessor(EVMContractProcessor):
    def __init__(self, db):
        super().__init__(db, "Base", Settings.BASE_ENDPOINT)
        self.db = db

