class MemoryCoreFunctions:
    def __init__(self, config: Dict):
        self.config = config
        self.mem0 = config['mem0']
        # Add new components
        self.context_manager = MemoryContextManager()
        self.validator = MemoryValidator()
        self.cache = MemoryCache()
        
    async def perform_operation(self, operation: str, **kwargs):
        try:
            # Validate input
            if 'content' in kwargs:
                validation_result = self.validator.validate_memory(
                    kwargs['content'], 
                    kwargs.get('metadata', {})
                )
                if not validation_result['is_valid']:
                    raise ValueError(validation_result['error'])
                    
            # Check cache first
            if operation == 'search':
                cached_result = await self.cache.get_cached_memory(
                    kwargs.get('query')
                )
                if cached_result:
                    return cached_result
                    
            # Update context
            if operation == 'add':
                await self.context_manager.manage_context([{
                    'content': kwargs['content'],
                    'metadata': kwargs.get('metadata', {})
                }])
                
            # Perform original operation
            result = await super().perform_operation(operation, **kwargs)
            
            # Cache results if applicable
            if operation == 'search':
                await self.cache.cache_memory(
                    kwargs.get('query'),
                    result
                )
                
            return result
            
        except Exception as e:
            capture_event(f"error.memory.{operation}", {"error": str(e)})
            raise