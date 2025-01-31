from ..evm_models.evm_pipeline import EVMPipeline
from .polygon_processor import PolygonChainProcessor
from .polygon_querier import PolygonChainQuerier

class PolygonChainPipeline(EVMPipeline):
    """
    Polygon-specific pipeline implementation.
    """
    def __init__(self, sql_database, mongodb_database):
        querier = PolygonChainQuerier()
        processor = PolygonChainProcessor(sql_database, mongodb_database, querier)
        super().__init__(
            sql_database=sql_database,
            mongodb_database=mongodb_database,
            network_name="polygon",
            querier=querier,
            processor=processor
        )

    async def stop(self):
        if hasattr(self, 'websocket_handler'):
            await self.websocket_handler.stop()
