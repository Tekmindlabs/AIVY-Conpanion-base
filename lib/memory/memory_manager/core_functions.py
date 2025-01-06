from typing import Dict, Any
from mem0.memory.telemetry import capture_event

class CoreFunctions:
    def __init__(self, config: Dict):
        self.config = config
        self.mem0 = config.mem0
        
    async def perform_operation(self, operation: str, **kwargs):
        """Execute core operations with telemetry"""
        try:
            capture_event(f"mem0.{operation}", self, kwargs)
            if operation == "add":
                return await self._add_memory(**kwargs)
            elif operation == "search":
                return await self._search_memory(**kwargs)
            elif operation == "update":
                return await self._update_memory(**kwargs)
        except Exception as e:
            capture_event(f"mem0.error.{operation}", self, {"error": str(e)})
            raise
            
    async def _add_memory(self, content: str, metadata: Dict[str, Any]):
        return await self.mem0.add(content=content, metadata=metadata)
        
    async def _search_memory(self, query: str, filters: Dict = None):
        return await self.mem0.search(query=query, filters=filters)
        
    async def _update_memory(self, memory_id: str, content: str):
        return await self.mem0.update(memory_id=memory_id, content=content)