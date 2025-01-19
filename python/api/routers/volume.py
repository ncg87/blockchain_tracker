from fastapi import APIRouter, Depends
from typing import Dict, List
import asyncpg
from ..database import get_db_pool
from ...database.queries.volume_queries import get_all_networks_volume_query

router = APIRouter()

INTERVALS = {
    "5m": 300,        # 5 minutes
    "1h": 3600,       # 1 hour
    "24h": 86400,     # 24 hours
    "1w": 604800,     # 1 week
}

@router.get("/all")
async def get_all_volumes(
    db_pool: asyncpg.Pool = Depends(get_db_pool)
) -> Dict[str, Dict[str, str]]:
    """Get trading volume for all networks across different time intervals"""
    result = {}
    
    async with db_pool.acquire() as conn:
        for interval_name, seconds in INTERVALS.items():
            query = get_all_networks_volume_query(seconds)
            rows = await conn.fetch(query)
            
            if not interval_name in result:
                result[interval_name] = {}
            
            for row in rows:
                network = row['network']
                volume = row['volume']
                
                # Convert to appropriate units (ETH, BTC, etc.)
                if network == 'Bitcoin':
                    volume = float(volume) / 100000000  # Convert satoshis to BTC
                else:
                    volume = float(volume) / 1e18  # Convert wei to ETH
                
                result[interval_name][network] = f"{volume:.4f}"
    
    return result 