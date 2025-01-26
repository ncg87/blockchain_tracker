from fastapi import APIRouter, HTTPException
from typing import Dict
from ..services.volume_service import VolumeService
from ..core.cache import get_cache, get_cache_value
from datetime import datetime
import logging
from asyncio import timeout

router = APIRouter()
volume_service = VolumeService()
logger = logging.getLogger(__name__)

# Cache data fetching function
async def get_cached_data() -> Dict:
    """Fetch all data that needs to be cached"""
    try:
        start_time = datetime.now()
        logger.info("Starting volume cache update...")
        
        cache_data = {
            'all_volumes': {},
            'all_fees': {},
            'all_tx_counts': {},
            'network_stats': {},
            'network_tokens': {},
            'historical_data': {}
        }
        
        async with timeout(30):  # 30 second timeout
            try:
                cache_data['all_volumes'] = await volume_service.get_all_volumes()
            except Exception as e:
                logger.error(f"Error fetching all volumes: {str(e)}")

            networks = ['Ethereum', 'Arbitrum', 'BNB', 'Base']
            for network in networks:
                try:
                    logger.info(f"Caching data for network: {network}")
                    cache_data['network_stats'][network] = await volume_service.get_network_stats(network, "24h")
                    cache_data['network_tokens'][network] = await volume_service.get_volume_of_all_tokens(network, "1h", 24)
                    cache_data['historical_data'][network] = await volume_service.get_network_historical_data(network, "1h", 24)
                except Exception as e:
                    logger.error(f"Error caching data for network {network}: {str(e)}")
                    cache_data['network_stats'][network] = None
                    cache_data['network_tokens'][network] = None
                    cache_data['historical_data'][network] = None
                    continue
            
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Volume cache update completed in {duration:.2f} seconds")
        return cache_data
    except Exception as e:
        logger.error(f"Error in volume cache update: {str(e)}")
        return {}

# Modified endpoints to use cache
@router.get("/all")
async def get_all_volumes() -> Dict[str, Dict[str, str]]:
    """Get volumes for all networks across different time intervals"""
    from main import cache
    try:
        return cache.get('volume', {}).get('all_volumes', {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/{network}")
async def get_network_stats(network: str, interval: str = "24h") -> Dict[str, float]:
    """Get comprehensive stats for a specific network"""
    from main import cache
    try:
        # Return cached data for common case (24h interval)
        if interval == "24h" and network in cache.get('volume', {}).get('network_stats', {}):
            return cache['volume']['network_stats'][network]
        # Fallback to direct service call for non-cached cases
        return await volume_service.get_network_stats(network, interval)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tokens/{network}")
async def get_volume_of_all_tokens(network: str, interval: str = "1h", points: int = 24) -> Dict[str, float]:
    """Get volume of all tokens for a specific network"""
    from main import cache
    try:
        # Return cached data for common case
        if interval == "1h" and points == 24 and network in cache.get('volume', {}).get('network_tokens', {}):
            return cache['volume']['network_tokens'][network]
        # Fallback to direct service call for non-cached cases
        return await volume_service.get_volume_of_all_tokens(network, interval, points)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fees/all")
async def get_all_fees() -> Dict[str, Dict[str, str]]:
    """Get fees for all networks across different time intervals"""
    from main import cache
    try:
        return cache.get('volume', {}).get('all_fees', {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transactions/all")
async def get_all_tx_counts() -> Dict[str, Dict[str, int]]:
    """Get transaction counts for all networks across different time intervals"""
    from main import cache
    try:
        return cache.get('volume', {}).get('all_tx_counts', {})
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
        if points <= 0 or points > 168:
            raise ValueError("Points must be between 1 and 168")
        
        cache = get_cache()
        volume_cache = cache.get('volume', {})
        
        # Return cached data for common case
        if interval == "1h" and points == 24 and network in volume_cache.get('historical_data', {}):
            return volume_cache['historical_data'][network]
            
        # Fallback to direct service call for non-cached cases
        result = await volume_service.get_network_historical_data(network, interval, points)
        if not result:
            raise HTTPException(status_code=404, detail=f"No data found for network: {network}")
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in historical endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching historical data")