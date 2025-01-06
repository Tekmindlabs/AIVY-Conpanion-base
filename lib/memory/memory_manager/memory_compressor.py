import logging
from typing import List, Dict, Optional
import zlib
import json

logger = logging.getLogger(__name__)

class MemoryCompressor:
    def __init__(self, compression_level: int = 6):
        self.compression_level = compression_level
        
    async def compress_memories(self, memories: List[Dict]) -> Dict:
        """
        Compresses memories for efficient storage
        """
        try:
            # Convert memories to JSON string
            memories_json = json.dumps(memories)
            
            # Compress the JSON string
            compressed_data = zlib.compress(
                memories_json.encode('utf-8'), 
                level=self.compression_level
            )
            
            compression_stats = {
                "original_size": len(memories_json),
                "compressed_size": len(compressed_data),
                "compression_ratio": len(memories_json) / len(compressed_data)
            }
            
            return {
                "compressed_data": compressed_data,
                "stats": compression_stats
            }
            
        except Exception as e:
            logger.error(f"Memory compression error: {str(e)}")
            return None
            
    async def decompress_memories(self, compressed_data: bytes) -> List[Dict]:
        """
        Decompresses stored memories
        """
        try:
            decompressed_data = zlib.decompress(compressed_data)
            return json.loads(decompressed_data.decode('utf-8'))
        except Exception as e:
            logger.error(f"Memory decompression error: {str(e)}")
            return None