class MemoryMaintenance:
    def __init__(self, config: Dict):
        self.mem0 = config['mem0']
        self.summarizer = MemorySummarizer(config.get('llm'))
        
    async def cleanup_memories(self, age_days: Optional[int] = 30):
        old_memories = await self.mem0.search(
            filters={"age_days": age_days}
        )
        
        # Summarize old memories before cleanup
        if old_memories:
            summary = await self.summarizer.summarize_memories(old_memories)
            if summary:
                await self.store_summary(summary)
                
        return await super().cleanup_memories(age_days)
        
    async def store_summary(self, summary: Dict):
        await self.mem0.add(
            content=summary['summary'],
            metadata={
                'type': 'memory_summary',
                'original_count': summary['original_count'],
                'timestamp': summary['timestamp']
            }
        )