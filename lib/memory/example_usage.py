# example_usage.py
import asyncio
from memory_manager import EnhancedMemoryManager
from config import DEFAULT_CONFIG

async def main():
    # Initialize memory manager
    memory_manager = EnhancedMemoryManager(DEFAULT_CONFIG)
    
    # Add memory
    memory_result = await memory_manager.add_memory(
        content="User prefers visual learning and enjoys programming in Python",
        user_id="user123",
        metadata={"type": "preference", "source": "chat"}
    )
    print(f"Memory added: {memory_result}")
    
    # Search memories
    search_results = await memory_manager.search_memories(
        query="What are the user's learning preferences?",
        user_id="user123",
        limit=5
    )
    print(f"Search results: {search_results}")

if __name__ == "__main__":
    asyncio.run(main())