import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MemoryCache:
    def __init__(self, ttl_seconds: int = 3600):
        self.cache = {}
        self.ttl_seconds = ttl_seconds
        
    async def get_cached_memory(self, memory_id: str) -> Optional[Dict]:
        """
        Retrieves cached memory if available and not expired
        """
        try:
            if memory_id in self.cache:
                cached_item = self.cache[memory_id]
                if not self._is_expired(cached_item['timestamp']):
                    return cached_item['data']
                else:
                    del self.cache[memory_id]
            return None
            
        except Exception as e:
            logger.error(f"Cache retrieval error: {str(e)}")
            return None
            
    async def cache_memory(self, memory_id: str, data: Dict) -> bool:
        """
        Caches memory data with TTL
        """
        try:
            self.cache[memory_id] = {
                'data': data,
                'timestamp': datetime.utcnow()
            }
            return True
        except Exception as e:
            logger.error(f"Cache storage error: {str(e)}")
            return False
            
    def _is_expired(self, timestamp: datetime) -> bool:
        """
        Checks if cached item has expired
        """
        return (datetime.utcnow() - timestamp).total_seconds() > self.ttl_seconds
        
    async def clear_expired(self):
        """
        Removes expired items from cache
        """
        try:
            current_time = datetime.utcnow()
            expired_keys = [
                k for k, v in self.cache.items() 
                if self._is_expired(v['timestamp'])
            ]
            for k in expired_keys:
                del self.cache[k]
        except Exception as e:
            logger.error(f"Cache cleanup error: {str(e)}")