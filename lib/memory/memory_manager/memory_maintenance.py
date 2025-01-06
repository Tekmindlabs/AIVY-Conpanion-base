import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MemoryMaintenance:
    async def update_memory(self, memory_id: str, content: str, metadata: Optional[Dict] = None) -> Dict:
        """Update an existing memory"""
        try:
            existing_memory = await self._get_memory(memory_id)
            if not existing_memory:
                raise ValueError(f"Memory with ID {memory_id} not found")
            
            metadata = metadata or {}
            metadata["updated_at"] = datetime.now().isoformat()
            metadata.update(existing_memory.get("metadata", {}))
            
            vector_id = await self._update_vector_store(memory_id, content, metadata)
            graph_id = await self._update_graph_db(memory_id, content, metadata)
            
            return {
                "status": "success",
                "vector_id": vector_id,
                "graph_id": graph_id,
                "timestamp": metadata["updated_at"]
            }
        except Exception as e:
            logger.error(f"Error updating memory: {str(e)}")
            raise

    async def delete_memory(self, memory_id: str) -> Dict:
        """Delete a specific memory"""
        try:
            await self.vector_store.delete(vector_id=memory_id)
            
            delete_query = """
            MATCH (m:Memory)
            WHERE id(m) = $memory_id
            DETACH DELETE m
            """
            self.graph.query(delete_query, {"memory_id": memory_id})
            
            return {
                "status": "success",
                "message": f"Memory {memory_id} deleted successfully"
            }
        except Exception as e:
            logger.error(f"Error deleting memory: {str(e)}")
            raise

    async def delete_all_memories(self, user_id: str) -> Dict:
        """Delete all memories for a user"""
        try:
            await self.vector_store.delete(f"metadata.user_id = '{user_id}'")
            
            delete_query = """
            MATCH (m:Memory {user_id: $user_id})
            DETACH DELETE m
            """
            self.graph.query(delete_query, {"user_id": user_id})
            
            return {
                "status": "success",
                "message": f"All memories for user {user_id} deleted successfully"
            }
        except Exception as e:
            logger.error(f"Error deleting all memories: {str(e)}")
            raise

    async def _get_memory(self, memory_id: str) -> Optional[Dict]:
        """Get a specific memory by ID"""
        try:
            memory = await self.vector_store.get(vector_id=memory_id)
            if not memory:
                return None
                
            return {
                "content": memory.page_content,
                "metadata": memory.metadata,
                "id": memory_id
            }
        except Exception as e:
            logger.error(f"Error getting memory: {str(e)}")
            raise

    async def _update_vector_store(self, memory_id: str, content: str, metadata: Dict) -> str:
        """Update content in vector store"""
        try:
            embeddings = self.embeddings.embed_documents([content])[0]
            
            await self.vector_store.update(
                vector_id=memory_id,
                vector=embeddings,
                metadata=metadata
            )
            
            return memory_id
        except Exception as e:
            logger.error(f"Error updating vector store: {str(e)}")
            raise

    async def _update_graph_db(self, memory_id: str, content: str, metadata: Dict) -> str:
        """Update content in graph database"""
        try:
            entities = await self._extract_entities(content)
            
            update_query = """
            MATCH (m:Memory)
            WHERE id(m) = $memory_id
            SET m.content = $content,
                m.timestamp = $timestamp
            WITH m
            MATCH (m)-[r:CONTAINS]->()
            DELETE r
            WITH m
            UNWIND $entities as entity
            MERGE (e:Entity {name: entity.name, type: entity.type})
            CREATE (m)-[:CONTAINS]->(e)
            RETURN id(m) as memory_id
            """
            
            result = self.graph.query(
                update_query,
                params={
                    "memory_id": memory_id,
                    "content": content,
                    "timestamp": metadata.get("timestamp", datetime.now().isoformat()),
                    "entities": entities
                }
            )
            
            return result[0]["memory_id"]
        except Exception as e:
            logger.error(f"Error updating graph DB: {str(e)}")
            raise