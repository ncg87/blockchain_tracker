from ..evm_models.evm_pipeline import EVMPipeline
from .avalanche_processor import AvalancheChainProcessor
from .avalanche_querier import AvalancheChainQuerier

class AvalancheChainPipeline(EVMPipeline):
    """
    Avalanche-specific pipeline implementation.
    """
    def __init__(self, sql_database, mongodb_database):
        querier = AvalancheChainQuerier()
        processor = AvalancheChainProcessor(sql_database, mongodb_database, querier)
        super().__init__(
            sql_database=sql_database,
            mongodb_database=mongodb_database,
            network_name="avalanche",
            querier=querier,
            processor=processor
        )

    async def stop(self):
        if hasattr(self, 'websocket_handler'):
            await self.websocket_handler.stop()
