from typing import List, Dict, Optional
from datetime import datetime
from .memory_manager import MemoryManager
from .config import DEFAULT_CONFIG

class MemoryService:
    def __init__(self, config: Dict = DEFAULT_CONFIG):
        self.memory_manager = MemoryManager(config)

    async def add_user_memory(
        self,
        user_id: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        if metadata is None:
            metadata = {}
        
        metadata["timestamp"] = datetime.now().isoformat()
        
        await self.memory_manager.add_memory(
            user_id=user_id,
            content=content,
            metadata=metadata
        )

    async def retrieve_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 5
    ):
        results = await self.memory_manager.search_memories(
            user_id=user_id,
            query=query,
            limit=limit
        )
        return results

    async def get_context(
        self,
        user_id: str,
        query: str,
        limit: int = 5
    ):
        # Get vector search results
        vector_results = await self.memory_manager.search_memories(
            user_id=user_id,
            query=query,
            limit=limit
        )

        # Get related memories from graph
        graph_results = await self.memory_manager.get_related_memories(
            user_id=user_id,
            content=query
        )

        # Combine and deduplicate results
        all_memories = {
            **{r.id: r for r in vector_results},
            **{r.id: r for r in graph_results}
        }

        return list(all_memories.values())