class StorageOperations:
    def __init__(self, config: Dict):
        self.mem0 = config['mem0']
        self.vector_store = config['vector_store']
        self.compressor = MemoryCompressor()
        
    async def store_memory(self, content: str, metadata: Dict):
        try:
            # Compress content if needed
            compression_result = await self.compressor.compress_memories([{
                'content': content,
                'metadata': metadata
            }])
            
            if compression_result:
                content = compression_result['compressed_data']
                metadata['compression_stats'] = compression_result['stats']
                
            return await super().store_memory(content, metadata)
            
        except Exception as e:
            logger.error(f"Storage error: {str(e)}")
            raise