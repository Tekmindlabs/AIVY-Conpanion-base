from fastapi import APIRouter, Depends
from typing import Dict, List
from .memory_service import MemoryService

router = APIRouter()
memory_service = MemoryService()

@router.post("/memories")
async def add_memory(
    user_id: str,
    content: str,
    metadata: Dict = None
):
    await memory_service.add_user_memory(
        user_id=user_id,
        content=content,
        metadata=metadata
    )
    return {"status": "success"}

@router.get("/memories/search")
async def search_memories(
    user_id: str,
    query: str,
    limit: int = 5
):
    results = await memory_service.retrieve_memories(
        user_id=user_id,
        query=query,
        limit=limit
    )
    return results

@router.get("/memories/context")
async def get_context(
    user_id: str,
    query: str,
    limit: int = 5
):
    context = await memory_service.get_context(
        user_id=user_id,
        query=query,
        limit=limit
    )
    return context