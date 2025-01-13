from ..evm_models import EVMProcessor

# Item getters 

class BNBProcessor(EVMProcessor):
    """
    BNB processor class.
    """
    def __init__(self, sql_database, mongodb_database, querier):
        """
        Initialize the BNB processor with a database and querier.
        """
        super().__init__(sql_database, mongodb_database, 'BNB', querier)  