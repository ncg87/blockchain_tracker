from ..evm_models.evm_pipeline import EVMPipeline
from .polygonzk_processor import PolygonZKProcessor
from .polygonzk_querier import PolygonZKQuerier

class PolygonZKPipeline(EVMPipeline):
    """
    Polygon zkEVM-specific pipeline implementation.
    """
    def __init__(self, sql_database, mongodb_database):
        querier = PolygonZKQuerier()
        processor = PolygonZKProcessor(sql_database, mongodb_database, querier)
        super().__init__(
            sql_database=sql_database,
            mongodb_database=mongodb_database,
            network_name="polygonzk",
            querier=querier,
            processor=processor
        )

    async def stop(self):
        if hasattr(self, 'websocket_handler'):
            await self.websocket_handler.stop() 