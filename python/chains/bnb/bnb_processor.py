from ..evm_models import EVMProcessor

class BNBProcessor(EVMProcessor):
    """
    BNB processor class.
    """
    def __init__(self, sql_database, mongodb_database, querier):
        """
        Initialize the BNB processor with a database and querier.
        """
        super().__init__(
            sql_database=sql_database,
            mongodb_database=mongodb_database,
            network_name='bnb',
            querier=querier
        )