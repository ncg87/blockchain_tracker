from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime
import sys
from .routers import volume, blocks, swaps
from fastapi_utils.tasks import repeat_every
from typing import Dict
import asyncio
from .core.cache import update_cache
from .routers.volume import get_cached_data
from .routers.swaps import get_cached_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Print to console
        logging.FileHandler('api.log')      # Save to file
    ]
)

logger = logging.getLogger(__name__)

# Add cache dictionary
cache: Dict[str, any] = {}

app = FastAPI(
    title="Blockchain Analytics API",
    description="API for accessing blockchain data and analytics",
    version="1.0.0"
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"], # TODO: change to production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
#app.include_router(blocks.router, prefix="/api/v1/blocks", tags=["blocks"])
#app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["transactions"])
#app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
#app.include_router(patterns.router, prefix="/api/v1/patterns", tags=["patterns"])
app.include_router(volume.router, prefix="/api/v1/volume", tags=["volume"])
app.include_router(swaps.router, prefix="/api/v1/swaps", tags=["swaps"])

# Remove this combined decorator as it can cause issues
# @app.on_event("startup")
@repeat_every(seconds=300)  # 5 minutes
async def update_cache_periodic():
    """Update cache every 5 minutes with latest data"""
    try:
        start_time = datetime.now()
        logger.info("Starting periodic cache update...")
        
        # Update cache for volume endpoint
        volume_data = await get_cached_data()
        update_cache('volume', volume_data)
        logger.info("Volume cache updated successfully")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Cache update completed in {duration:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Error updating cache: {str(e)}", exc_info=True)

@app.middleware("http")
async def log_requests(request, call_next):
    """Log all incoming requests and their processing time"""
    start_time = datetime.now()
    response = await call_next(request)
    duration = (datetime.now() - start_time).total_seconds()
    
    logger.info(
        f"Path: {request.url.path} - "
        f"Method: {request.method} - "
        f"Status: {response.status_code} - "
        f"Duration: {duration:.2f}s"
    )
    
    return response

# Modify root endpoint to include cache status
@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {
        "message": "Welcome to the Blockchain Analytics API",
        "cache_status": "active" if cache else "initializing"
    }

@app.on_event("startup")
async def startup_event():
    """Initialize cache on startup"""
    try:
        logger.info("Starting initial cache population...")
        # Initialize volume cache
        volume_data = await get_cached_data()
        update_cache('volume', volume_data)
        
        # Schedule the periodic updates
        asyncio.create_task(update_cache_periodic())
        
        logger.info("Cache initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing cache: {str(e)}", exc_info=True)