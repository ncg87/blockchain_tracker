from ..evm_models import EVMProcessor

class ArbitrumProcessor(EVMProcessor):
    """
    Arbitrum processor class.
    """
    def __init__(self, sql_database, mongodb_database, querier):
        """
        Initialize the processor with a database instance.
        """
        super().__init__(
            sql_database=sql_database,
            mongodb_database=mongodb_database,
            network_name="arbitrum",
            querier=querier
        )