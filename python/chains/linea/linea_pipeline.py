from ..evm_models.evm_pipeline import EVMPipeline
from .linea_processor import LineaProcessor
from .linea_querier import LineaQuerier

class LineaPipeline(EVMPipeline):
    """
    Linea-specific pipeline implementation.
    """
    def __init__(self, sql_database, mongodb_database):
        querier = LineaQuerier()
        processor = LineaProcessor(sql_database, mongodb_database, querier)
        super().__init__(
            sql_database=sql_database,
            mongodb_database=mongodb_database,
            network_name="linea",
            querier=querier,
            processor=processor
        )

    async def stop(self):
        if hasattr(self, 'websocket_handler'):
            await self.websocket_handler.stop()
