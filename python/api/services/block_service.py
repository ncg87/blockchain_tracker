from typing import List, Optional
from database import SQLQueryOperations, MongoQueryOperations
from database import SQLDatabase, MongoDatabase

class BlockService:
    def __init__(self):
        self.sql_db = SQLDatabase()
        self.mongo_db = MongoDatabase()
        self.sql_query = SQLQueryOperations(self.sql_db)
        self.mongo_query = MongoQueryOperations(self.mongo_db)

    async def get_blocks(
        self, 
        network: str, 
        start_block: Optional[int] = None,
        end_block: Optional[int] = None,
        limit: int = 10
    ) -> List[dict]:
        """Get blocks with optional range filtering"""
        blocks = self.sql_query.query_by_network(
            network=network,
            start_block=start_block,
            end_block=end_block,
            limit=limit
        )
        
        # Enrich with MongoDB data
        for block in blocks:
            mongo_data = self.mongo_query.get_block_by_number(
                network=network,
                block_number=block['block_number']
            )
            if mongo_data:
                block['additional_data'] = mongo_data
                
        return blocks

    async def get_latest_block(self, network: str) -> dict:
        """Get the latest block for a network"""
        return self.sql_query.query_by_network(network, limit=1)[0]