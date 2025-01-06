"""
Memory management module initialization.
This module provides memory management functionality using Google Generative AI, 
Milvus, Neo4j, and Jina with Langchain integration.
"""

import importlib.metadata

# Version information
try:
    __version__ = importlib.metadata.version("mem0ai")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"

# Import main components
from lib.memory.memory_manager import EnhancedMemoryManager
from lib.memory.config import DEFAULT_CONFIG

# Define public interface
__all__ = [
    "EnhancedMemoryManager",
    "DEFAULT_CONFIG",
]

# Module level docstring
__doc__ = """
Memory Management Module
=======================

This module provides enhanced memory management capabilities using:
- Google Generative AI for LLM operations
- Milvus for vector storage
- Neo4j for graph-based memory storage
- Jina for embeddings
- Langchain for chain and memory management

Main Components:
---------------
- EnhancedMemoryManager: Main class for memory operations
- DEFAULT_CONFIG: Default configuration settings

Example Usage:
-------------
    from lib.memory import EnhancedMemoryManager, DEFAULT_CONFIG
    
    memory_manager = EnhancedMemoryManager(DEFAULT_CONFIG)
    
    # Add memory
    await memory_manager.add_memory(
        content="User prefers visual learning",
        user_id="user123"
    )
    
    # Search memories
    results = await memory_manager.search_memories(
        query="learning preferences",
        user_id="user123"
    )
"""

# Optional: Add any initialization code if needed
def setup():
    """Initialize any required components or settings."""
    pass

# Run setup if needed
setup()