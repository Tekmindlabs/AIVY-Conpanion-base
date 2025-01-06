import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class MemoryContextManager:
    def __init__(self, max_context_size: int = 10):
        self.context_window = []
        self.max_context_size = max_context_size
        
    async def manage_context(self, messages: List[Dict]) -> List[Dict]:
        """
        Manages the context window for memory operations
        """
        try:
            # Add new messages to context
            self.context_window.extend(messages)
            
            # Trim context if it exceeds max size
            if len(self.context_window) > self.max_context_size:
                self.context_window = self.context_window[-self.max_context_size:]
                
            # Remove duplicates while preserving order
            seen = set()
            deduplicated_context = []
            for msg in self.context_window:
                msg_hash = hash(str(msg))
                if msg_hash not in seen:
                    seen.add(msg_hash)
                    deduplicated_context.append(msg)
                    
            self.context_window = deduplicated_context
            return self.context_window
            
        except Exception as e:
            logger.error(f"Error in context management: {str(e)}")
            return messages
            
    async def get_relevant_context(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Retrieves relevant context based on query
        """
        # Implement relevance scoring and filtering
        return self.context_window[:limit]