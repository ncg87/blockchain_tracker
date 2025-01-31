from ..evm_models.evm_pipeline import EVMPipeline
from .zksync_processor import ZkSyncProcessor
from .zksync_querier import ZkSyncQuerier

class ZkSyncPipeline(EVMPipeline):
    """
    zkSync-specific pipeline implementation.
    """
    def __init__(self, sql_database, mongodb_database):
        querier = ZkSyncQuerier()
        processor = ZkSyncProcessor(sql_database, mongodb_database, querier)
        super().__init__(
            sql_database=sql_database,
            mongodb_database=mongodb_database,
            network_name="zksync",
            querier=querier,
            processor=processor
        )

    async def stop(self):
        if hasattr(self, 'websocket_handler'):
            await self.websocket_handler.stop() 