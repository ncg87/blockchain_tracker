from ..evm_models.evm_pipeline import EVMPipeline
from .mantle_processor import MantleProcessor
from .mantle_querier import MantleQuerier

class MantlePipeline(EVMPipeline):
    """
    Mantle-specific pipeline implementation.
    """
    def __init__(self, sql_database, mongodb_database):
        querier = MantleQuerier()
        processor = MantleProcessor(sql_database, mongodb_database, querier)
        super().__init__(
            sql_database=sql_database,
            mongodb_database=mongodb_database,
            network_name="mantle",
            querier=querier,
            processor=processor
        )

    async def stop(self):
        if hasattr(self, 'websocket_handler'):
            await self.websocket_handler.stop() 