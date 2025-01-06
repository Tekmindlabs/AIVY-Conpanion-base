from typing import Dict, List
from datetime import datetime

class StorageOperations:
    def __init__(self, config: Dict):
        self.mem0 = config.mem0
        self.vector_store = config.vector_store
        
    async def store_memory(self, content: str, metadata: Dict):
        """Store memory with proper tracking"""
        memory_id = await self.mem0.add(
            content=content,
            metadata={
                **metadata,
                "timestamp": datetime.utcnow().isoformat(),
                "hash": self._generate_hash(content)
            }
        )
        
        await self._store_vectors(memory_id, content)
        return memory_id
        
    async def _store_vectors(self, memory_id: str, content: str):
        """Store vector embeddings"""
        self.vector_store.add_texts(
            texts=[content],
            metadatas=[{"memory_id": memory_id}]
        )
        
    async def _track_history(self, memory_id: str, prev_value: str, new_value: str, operation: str):
        """Track memory changes"""
        return await self.mem0.db.add_history(
            memory_id=memory_id,
            prev_value=prev_value,
            new_value=new_value,
            operation=operation
        )
        
    def _generate_hash(self, content: str) -> str:
        """Generate hash for deduplication"""
        return self.mem0.utils.generate_hash(content)