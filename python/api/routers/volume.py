from fastapi import APIRouter, Depends
from typing import Dict
from python.api.dependencies import get_db
from ...database.sql.operations.api import APIQueryOperations

router = APIRouter()

INTERVALS = {
    "5m": 300,
    "1h": 3600,
    "24h": 86400,
    "1w": 604800,
}

@router.get("/volume/all")
async def get_all_volumes(db = Depends(get_db)) -> Dict[str, Dict[str, str]]:
    api_ops = APIQueryOperations(db)
    result = {}
    
    for interval_name, seconds in INTERVALS.items():
        volumes = api_ops.get_all_networks_volume(seconds)
        result[interval_name] = {
            network: f"{volume:.4f}" 
            for network, volume in volumes.items()
        }
    
    return result

@router.get("/stats/{network}")
async def get_network_stats(
    network: str, 
    interval: str = "24h", 
    db = Depends(get_db)
) -> Dict[str, float]:
    if interval not in INTERVALS:
        raise HTTPException(status_code=400, detail="Invalid interval")
    
    api_ops = APIQueryOperations(db)
    return api_ops.get_network_stats(network, INTERVALS[interval])