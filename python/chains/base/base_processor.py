from ..evm_models.evm_processor import EVMProcessor

class BaseChainProcessor(EVMProcessor):
    """
    Base-specific processor implementation.
    """
    def __init__(self, sql_database, mongodb_database, querier):
        super().__init__(
            sql_database=sql_database,
            mongodb_database=mongodb_database,
            network_name="base",
            querier=querier
        )
