from ..evm_models import EVMPipeline
from .arbitrum_processor import ArbitrumProcessor
from .arbitrum_querier import ArbitrumQuerier

class ArbitrumPipeline(EVMPipeline):
    """
    Arbitrum pipeline class supporting asynchronous block streaming.
    """
    def __init__(self, sql_database, mongodb_database):
        # Initialize querier and processor
        querier = ArbitrumQuerier()
        processor = ArbitrumProcessor(sql_database, mongodb_database, querier)
        # Initialize pipeline
        super().__init__(
            sql_database=sql_database,
            mongodb_database=mongodb_database,
            network_name="arbitrum",
            querier=querier,
            processor=processor
        )
    async def stop(self):
        if hasattr(self, 'websocket_handler'):
            await self.websocket_handler.stop()