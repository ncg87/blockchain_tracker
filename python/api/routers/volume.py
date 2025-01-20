from fastapi import APIRouter, HTTPException
from typing import Dict
from ..services.volume_service import VolumeService

router = APIRouter()
volume_service = VolumeService()

@router.get("/all")
async def get_all_volumes() -> Dict[str, Dict[str, str]]:
    """Get volumes for all networks across different time intervals"""
    try:
        return await volume_service.get_all_volumes()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/{network}")
async def get_network_stats(network: str, interval: str = "24h") -> Dict[str, float]:
    """Get comprehensive stats for a specific network"""
    try:
        return await volume_service.get_network_stats(network, interval)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fees/all")
async def get_all_fees() -> Dict[str, Dict[str, str]]:
    """Get fees for all networks across different time intervals"""
    try:
        return await volume_service.get_all_fees()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transactions/all")
async def get_all_tx_counts() -> Dict[str, Dict[str, int]]:
    """Get transaction counts for all networks across different time intervals"""
    try:
        result = await volume_service.get_all_tx_counts()
                    
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/historical/{network}")
async def get_network_historical_data(
    network: str, 
    interval: str = "1h", 
    points: int = 24
) -> Dict:
    """Get historical data points for a specific network"""
    try:
        if points <= 0 or points > 168:  # Max 1 week of hourly data
            raise ValueError("Points must be between 1 and 168")
            
        result = await volume_service.get_network_historical_data(network, interval, points)
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for network: {network}"
            )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Unexpected error in historical endpoint: {str(e)}")  # For debugging
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while fetching historical data"
        )