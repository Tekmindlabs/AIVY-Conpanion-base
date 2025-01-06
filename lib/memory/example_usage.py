from memory_manager import EnhancedMemoryManager
from config import DEFAULT_CONFIG

async def main():
    # Initialize manager
    memory_manager = EnhancedMemoryManager(DEFAULT_CONFIG)
    
    # Check health
    health_status = await memory_manager.health_check()
    print(f"System health: {health_status}")
    
    # Add memory
    result = await memory_manager.add_memory(
        content="User prefers visual learning",
        user_id="user123",
        metadata={"type": "preference"}
    )
    
    # Get statistics
    stats = await memory_manager.get_memory_stats("user123")
    print(f"Memory stats: {stats}")
    
    # Cleanup old memories
    await memory_manager.cleanup_old_memories("user123", days_old=30)
    
    # Disconnect
    await memory_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(main())