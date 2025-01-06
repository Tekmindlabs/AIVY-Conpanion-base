from typing import Dict, List, Optional
from langchain.schema import BaseMessage as LangChainBaseMessage
from mem0.memory.main import Memory as Mem0Memory

class BaseMessage(LangChainBaseMessage):
    """Base message class inheriting from LangChain's BaseMessage"""
    def __init__(self, content: str, additional_kwargs: Optional[Dict] = None):
        super().__init__(content=content, additional_kwargs=additional_kwargs)
        
class ChatMessage(BaseMessage):
    """Chat message implementation"""
    type = "chat"
    
    def __init__(self, content: str, role: str, metadata: Optional[Dict] = None):
        super().__init__(content=content, additional_kwargs={"role": role, "metadata": metadata})