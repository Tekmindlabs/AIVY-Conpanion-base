import logging
import asyncio
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class BaseMessage:
    """Base class for all message types"""
    def __init__(self, content: str, creator: str, metadata: Optional[Dict] = None):
        self.content = content
        self.creator = creator
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()
        
    def to_dict(self) -> Dict:
        return {
            "content": self.content,
            "creator": self.creator,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }

class ChatMessage(BaseMessage):
    """Specialized message class for chat interactions"""
    def __init__(self, 
                 human_message: Optional[str] = None, 
                 ai_message: Optional[str] = None,
                 metadata: Optional[Dict] = None):
        super().__init__(content=human_message or "", creator="human", metadata=metadata)
        self.human_message = human_message
        self.ai_message = ai_message
        
    def to_dict(self) -> Dict:
        base_dict = super().to_dict()
        base_dict.update({
            "human_message": self.human_message,
            "ai_message": self.ai_message
        })
        return base_dict