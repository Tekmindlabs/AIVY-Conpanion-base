from typing import Dict, Optional
from datetime import datetime

class MemoryMaintenance:
    def __init__(self, config: Dict):
        self.mem0 = config.mem0
        
    async def update_memory(self, memory_id: str, content: str):
        """Update memory with version tracking"""
        prev_version = await self.mem0.get(memory_id)
        
        result = await self.mem0.update(
            memory_id=memory_id,
            content=content,
            metadata={
                "updated_at": datetime.utcnow().isoformat(),
                "previous_version": prev_version
            }
        )
        
        await self._track_history(memory_id, prev_version, content, "UPDATE")
        return result
        
    async def cleanup_memories(self, age_days: Optional[int] = 30):
        """Implement memory cleanup"""
        return await self.mem0.cleanup(
            filters={
                "age_days": age_days
            }
        )
        
    async def maintain_indexes(self):
        """Maintain database indexes"""
        await self.mem0.db.optimize_indexes()