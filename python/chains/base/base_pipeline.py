from ..evm_models.evm_pipeline import EVMPipeline
from .base_processor import BaseChainProcessor
from .base_querier import BaseChainQuerier

class BaseChainPipeline(EVMPipeline):
    """
    Base-specific pipeline implementation.
    """
    def __init__(self, sql_database, mongodb_database):
        querier = BaseChainQuerier()
        processor = BaseChainProcessor(sql_database, mongodb_database, querier)
        super().__init__(
            sql_database=sql_database,
            mongodb_database=mongodb_database,
            network_name="Base",
            querier=querier,
            processor=processor
        )
    async def stop(self):
        if hasattr(self, 'websocket_handler'):
            await self.websocket_handler.stop()