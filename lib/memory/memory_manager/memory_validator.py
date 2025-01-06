import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MemoryValidator:
    REQUIRED_FIELDS = ['content', 'timestamp', 'user_id']
    MAX_CONTENT_LENGTH = 10000
    
    @staticmethod
    def validate_memory(content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates memory content and metadata
        """
        try:
            # Check required fields
            for field in MemoryValidator.REQUIRED_FIELDS:
                if field not in metadata:
                    raise ValueError(f"Missing required field: {field}")
                    
            # Validate content
            if not content or len(content) > MemoryValidator.MAX_CONTENT_LENGTH:
                raise ValueError("Invalid content length")
                
            # Validate metadata types
            if not isinstance(metadata.get('timestamp'), (int, float)):
                raise ValueError("Invalid timestamp format")
                
            if not isinstance(metadata.get('user_id'), str):
                raise ValueError("Invalid user_id format")
                
            return {
                "is_valid": True,
                "content": content,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Memory validation error: {str(e)}")
            return {
                "is_valid": False,
                "error": str(e)
            }