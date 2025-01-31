from ..evm_models.evm_processor import EVMProcessor

class MantleProcessor(EVMProcessor):
    """
    Mantle-specific processor implementation.
    """
    def __init__(self, sql_database, mongodb_database, querier):
        super().__init__(
            sql_database=sql_database,
            mongodb_database=mongodb_database,
            network_name="mantle",
            querier=querier
        ) 