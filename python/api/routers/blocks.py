from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from ..services.block_service import BlockService
from ..models.schemas import BlockResponse

router = APIRouter()
block_service = BlockService()

@router.get("/{network}", response_model=List[BlockResponse])
async def get_blocks(
    network: str,
    start_block: Optional[int] = Query(None),
    end_block: Optional[int] = Query(None),
    limit: int = Query(10, le=100)
):
    """Get blocks for a specific network with optional range"""
    try:
        blocks = await block_service.get_blocks(network, start_block, end_block, limit)
        return blocks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{network}/latest")
async def get_latest_block(network: str):
    """Get the latest block for a specific network"""
    try:
        block = await block_service.get_latest_block(network)
        return block
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))