from ..evm_models.evm_pipeline import EVMPipeline
from .optimism_processor import OptimismChainProcessor
from .optimism_querier import OptimismChainQuerier

class OptimismChainPipeline(EVMPipeline):
    """
    Optimism-specific pipeline implementation.
    """
    def __init__(self, sql_database, mongodb_database):
        querier = OptimismChainQuerier()
        processor = OptimismChainProcessor(sql_database, mongodb_database, querier)
        super().__init__(
            sql_database=sql_database,
            mongodb_database=mongodb_database,
            network_name="optimism",
            querier=querier,
            processor=processor
        )

    async def stop(self):
        if hasattr(self, 'websocket_handler'):
            await self.websocket_handler.stop()
