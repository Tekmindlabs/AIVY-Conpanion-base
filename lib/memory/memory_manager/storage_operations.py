"""Storage operations for memory management."""
import logging
from typing import Dict, List, Optional
from datetime import datetime
from langchain_community.vectorstores import Milvus
from langchain_community.graphs import Neo4jGraph

logger = logging.getLogger(__name__)

class StorageOperations:
    def __init__(self, vector_store: Milvus, graph_db: Neo4jGraph):
        self.vector_store = vector_store
        self.graph_db = graph_db

    async def add_memory(self, content: str, user_id: str, metadata: Optional[Dict] = None) -> Dict:
        """
        Add a new memory to both vector and graph stores.
        
        Args:
            content: The memory content to store
            user_id: The user ID associated with the memory
            metadata: Optional metadata for the memory
            
        Returns:
            Dict containing storage operation results
        """
        try:
            # Prepare metadata
            metadata = metadata or {}
            metadata.update({
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "type": "memory"
            })

            # Store in vector database
            vector_id = await self._store_in_vector_db(content, user_id, metadata)
            
            # Store in graph database
            graph_id = await self._store_in_graph_db(content, user_id, metadata)

            return {
                "status": "success",
                "vector_id": vector_id,
                "graph_id": graph_id,
                "timestamp": metadata["timestamp"]
            }

        except Exception as e:
            logger.error(f"Error adding memory: {str(e)}")
            raise

    async def _store_in_vector_db(self, content: str, user_id: str, metadata: Dict) -> str:
        """
        Store memory in Milvus vector database.
        
        Args:
            content: Memory content
            user_id: User ID
            metadata: Memory metadata
            
        Returns:
            Vector store document ID
        """
        try:
            # Generate embeddings and store
            vector_ids = await self.vector_store.aadd_texts(
                texts=[content],
                metadatas=[metadata]
            )
            
            logger.info(f"Stored memory in vector store with ID: {vector_ids[0]}")
            return vector_ids[0]

        except Exception as e:
            logger.error(f"Error storing in vector DB: {str(e)}")
            raise

    async def _store_in_graph_db(self, content: str, user_id: str, metadata: Dict) -> str:
        """
        Store memory in Neo4j graph database.
        
        Args:
            content: Memory content
            user_id: User ID
            metadata: Memory metadata
            
        Returns:
            Graph node ID
        """
        try:
            # Extract entities for relationship mapping
            entities = await self._extract_entities(content)
            
            # Create memory node and relationships
            create_query = """
            CREATE (m:Memory {
                content: $content,
                user_id: $user_id,
                timestamp: $timestamp
            })
            WITH m
            UNWIND $entities as entity
            MERGE (e:Entity {name: entity.name, type: entity.type})
            CREATE (m)-[:CONTAINS]->(e)
            RETURN id(m) as memory_id
            """
            
            result = self.graph_db.query(
                create_query,
                params={
                    "content": content,
                    "user_id": user_id,
                    "timestamp": metadata["timestamp"],
                    "entities": entities
                }
            )
            
            memory_id = result[0]["memory_id"]
            logger.info(f"Stored memory in graph DB with ID: {memory_id}")
            return str(memory_id)

        except Exception as e:
            logger.error(f"Error storing in graph DB: {str(e)}")
            raise

    async def search_memories(self, query: str, user_id: str, limit: int = 5) -> List[Dict]:
        """
        Search for memories across both vector and graph stores.
        
        Args:
            query: Search query
            user_id: User ID
            limit: Maximum number of results
            
        Returns:
            List of matching memories
        """
        try:
            # Vector search
            vector_results = await self.vector_store.asimilarity_search_with_score(
                query=query,
                k=limit,
                filter={"user_id": user_id}
            )

            # Graph search
            graph_results = await self._search_graph_db(query, user_id)

            # Merge and rank results
            combined_results = self._merge_and_rank_results(
                vector_results=vector_results,
                graph_results=graph_results
            )

            return combined_results[:limit]

        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            raise

    async def batch_add_memories(self, memories: List[Dict]) -> Dict:
        """
        Batch add multiple memories.
        
        Args:
            memories: List of memory dictionaries containing content and metadata
            
        Returns:
            Dict containing operation results
        """
        try:
            results = {
                "successful": [],
                "failed": []
            }

            for memory in memories:
                try:
                    result = await self.add_memory(
                        content=memory["content"],
                        user_id=memory["user_id"],
                        metadata=memory.get("metadata")
                    )
                    results["successful"].append({
                        "content": memory["content"],
                        "result": result
                    })
                except Exception as e:
                    results["failed"].append({
                        "content": memory["content"],
                        "error": str(e)
                    })

            return results

        except Exception as e:
            logger.error(f"Error in batch memory addition: {str(e)}")
            raise

    async def get_related_memories(self, memory_id: str, user_id: str, limit: int = 5) -> List[Dict]:
        """
        Get memories related to a specific memory.
        
        Args:
            memory_id: Source memory ID
            user_id: User ID
            limit: Maximum number of related memories
            
        Returns:
            List of related memories
        """
        try:
            # Get related memories through graph relationships
            related_query = """
            MATCH (m:Memory {user_id: $user_id})-[:CONTAINS]->(e:Entity)
            <-[:CONTAINS]-(related:Memory)
            WHERE id(m) = $memory_id AND related.user_id = $user_id
            WITH related, count(e) as common_entities
            ORDER BY common_entities DESC
            LIMIT $limit
            RETURN related.content as content,
                   related.timestamp as timestamp,
                   common_entities as relevance_score
            """
            
            results = self.graph_db.query(
                related_query,
                params={
                    "memory_id": memory_id,
                    "user_id": user_id,
                    "limit": limit
                }
            )

            return [
                {
                    "content": record["content"],
                    "timestamp": record["timestamp"],
                    "relevance_score": record["relevance_score"]
                }
                for record in results
            ]

        except Exception as e:
            logger.error(f"Error getting related memories: {str(e)}")
            raise