import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import asyncio

logger = logging.getLogger(__name__)

class MemoryCoreFunctions:
    async def cleanup_old_memories(self, user_id: str, days_old: int = 30) -> None:
        """Remove memories older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # Clean vector store
            await self.vector_store.delete(
                f"metadata.timestamp < '{cutoff_date.isoformat()}' AND metadata.user_id = '{user_id}'"
            )
            
            # Clean Neo4j
            cleanup_query = """
            MATCH (m:Memory {user_id: $user_id})
            WHERE m.timestamp < $cutoff_date
            DETACH DELETE m
            """
            self.graph.query(cleanup_query, {
                "user_id": user_id,
                "cutoff_date": cutoff_date.isoformat()
            })
            
            logger.info(f"Cleaned up old memories for user {user_id}")
        except Exception as e:
            logger.error(f"Error cleaning up memories: {str(e)}")
            raise

    async def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """Get memory usage statistics"""
        try:
            vector_count = await self.vector_store.count(
                filter=f"metadata.user_id = '{user_id}'"
            )
            
            stats_query = """
            MATCH (m:Memory {user_id: $user_id})
            RETURN count(m) as memory_count,
                   count(()-[:CONTAINS]->()) as relationship_count
            """
            graph_stats = self.graph.query(stats_query, {"user_id": user_id})[0]
            
            return {
                "vector_memories": vector_count,
                "graph_memories": graph_stats["memory_count"],
                "relationships": graph_stats["relationship_count"]
            }
        except Exception as e:
            logger.error(f"Error getting memory stats: {str(e)}")
            raise

    async def health_check(self) -> Dict[str, bool]:
        """Check health of all components"""
        status = {
            "vector_store": False,
            "graph_db": False,
            "llm": False,
            "embeddings": False
        }
        
        try:
            # Check each component
            await self._check_vector_store(status)
            await self._check_graph_db(status)
            await self._check_llm(status)
            await self._check_embeddings(status)
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            
        return status

    def _process_entities(self, entities_text: str) -> List[Dict]:
        """Process and validate extracted entities"""
        try:
            if isinstance(entities_text, str):
                import ast
                entities = ast.literal_eval(entities_text)
            else:
                entities = entities_text
                
            validated_entities = []
            for entity in entities:
                if isinstance(entity, dict) and "name" in entity and "type" in entity:
                    validated_entities.append({
                        "name": str(entity["name"]),
                        "type": str(entity["type"])
                    })
                    
            return validated_entities
        except Exception as e:
            logger.error(f"Error processing entities: {str(e)}")
            return []