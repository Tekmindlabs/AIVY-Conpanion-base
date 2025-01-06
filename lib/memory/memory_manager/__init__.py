# Update __init__.py to include new components:
"""Memory management module initialization."""
from .base_classes import BaseMessage, ChatMessage
from .initialization_config import EnhancedMemoryManager
from .core_functions import MemoryCoreFunctions
from .storage_operations import StorageOperations
from .search_processing import SearchProcessing
from .memory_maintenance import MemoryMaintenance
# Add new imports
from .memory_context_manager import MemoryContextManager
from .memory_summarizer import MemorySummarizer
from .memory_validator import MemoryValidator
from .memory_compressor import MemoryCompressor
from .memory_cache import MemoryCache

__all__ = [
    'BaseMessage',
    'ChatMessage', 
    'EnhancedMemoryManager',
    'MemoryCoreFunctions',
    'StorageOperations',
    'SearchProcessing',
    'MemoryMaintenance',
    # Add new components
    'MemoryContextManager',
    'MemorySummarizer',
    'MemoryValidator',
    'MemoryCompressor',
    'MemoryCache'
]