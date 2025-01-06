# mem0_bridge.py
import os
import logging
import google.generativeai as genai
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class Mem0Bridge:
    def __init__(self):
        """Initialize the Mem0Bridge with configuration and memory system."""
        try:
            # Configuration for Google Gen AI, Milvus, Neo4j and Jina
            self.config = {
                "vector_store": {
                    "provider": "milvus",
                    "config": {
                        "collection_name": "aivy_memories",
                        "url": os.getenv("MILVUS_URL"),
                        "embedding_model_dims": 768,  # For Jina embeddings
                        "token": os.getenv("MILVUS_TOKEN"),
                        "metric_type": "L2"
                    }
                },
                "graph_store": {  # Neo4j configuration
                    "provider": "neo4j",
                    "config": {
                        "url": os.getenv("NEO4J_URL"),
                        "username": os.getenv("NEO4J_USER"),
                        "password": os.getenv("NEO4J_PASSWORD")
                    }
                },
                "llm": {
                    "provider": "google",
                    "config": {
                        "api_key": os.getenv("GOOGLE_API_KEY"),
                        "model": "gemini-pro",
                        "temperature": 0.1,
                        "max_tokens": 2000,
                    }
                },
                "embedder": {
                    "provider": "jina",
                    "config": {
                        "model": "jina-embeddings-v2-base-en",
                        "embedding_dims": 768
                    }
                },
                "version": "v1.1"
            }
            
            # Initialize Google Gen AI
            genai.configure(api_key=self.config["llm"]["config"]["api_key"])
            
            # Initialize memory system
            self.memory = Memory.from_config(self.config)
            logger.info("Memory system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Memory system: {str(e)}")
            self.memory = None
            raise

    def add_memory(self, content: str, user_id: str, metadata: Optional[Dict] = None) -> Dict:
        """Add a new memory."""
        try:
            messages = [{"role": "user", "content": content}]
            result = self.memory.add(
                messages=messages,
                user_id=user_id,
                metadata=metadata
            )
            return result
        except Exception as e:
            logger.error(f"Error adding memory: {str(e)}")
            return {"success": False, "error": str(e)}

    def search_memories(self, query: str, user_id: str, limit: int = 10) -> Dict:
        """Search memories based on query."""
        try:
            results = self.memory.search(
                query=query,
                user_id=user_id,
                limit=limit
            )
            return {"success": True, "results": results}
        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            return {"success": False, "error": str(e)}

    def delete_memory(self, memory_id: str, user_id: str) -> Dict:
        """Delete a specific memory."""
        try:
            result = self.memory.delete(memory_id=memory_id, user_id=user_id)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Error deleting memory: {str(e)}")
            return {"success": False, "error": str(e)}

class Memory:
    def __init__(self):
        self.vector_store = None
        self.graph_store = None
        self.llm = None
        self.embedder = None

    @classmethod
    def from_config(cls, config: Dict[str, Any]):
        instance = cls()
        try:
            # Configure Vector Store (Milvus)
            if "vector_store" in config:
                vector_config = config["vector_store"]
                instance.vector_store = {
                    "collection_name": vector_config["config"].get("collection_name"),
                    "url": vector_config["config"].get("url"),
                    "token": vector_config["config"].get("token"),
                    "embedding_dims": vector_config["config"].get("embedding_model_dims"),
                    "metric_type": vector_config["config"].get("metric_type")
                }

            # Configure Graph Store (Neo4j)
            if "graph_store" in config:
                graph_config = config["graph_store"]
                instance.graph_store = {
                    "url": graph_config["config"].get("url"),
                    "username": graph_config["config"].get("username"),
                    "password": graph_config["config"].get("password")
                }

            # Configure LLM and Embedder
            instance.llm = config.get("llm")
            instance.embedder = config.get("embedder")

            return instance
        except Exception as e:
            logger.error(f"Error configuring Memory: {str(e)}")
            raise

    def add(self, messages: List[Dict[str, str]], user_id: str, metadata: Optional[Dict] = None) -> Dict:
        """Add memory to both vector and graph stores."""
        try:
            # Process messages and metadata
            content = "\n".join([msg["content"] for msg in messages])
            
            # Generate embeddings
            embedding = self.embedder.embed(content)
            
            # Store in vector database
            vector_id = self._store_in_vector_db(content, embedding, user_id, metadata)
            
            # Store in graph database
            graph_id = self._store_in_graph_db(content, user_id, metadata)
            
            return {
                "success": True,
                "vector_id": vector_id,
                "graph_id": graph_id
            }
        except Exception as e:
            logger.error(f"Error adding memory: {str(e)}")
            return {"success": False, "error": str(e)}

    def search(self, query: str, user_id: str, limit: int = 10) -> List[Dict]:
        """Search memories using both vector and graph stores."""
        try:
            # Generate query embedding
            query_embedding = self.embedder.embed(query)
            
            # Search vector store
            vector_results = self._search_vector_db(query_embedding, user_id, limit)
            
            # Search graph store
            graph_results = self._search_graph_db(query, user_id, limit)
            
            # Combine and rank results
            combined_results = self._merge_search_results(vector_results, graph_results)
            
            return combined_results[:limit]
        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            return []

    def delete(self, memory_id: str, user_id: Optional[str] = None) -> Dict:
        """Delete memory from both stores."""
        try:
            # Delete from vector store
            vector_result = self._delete_from_vector_db(memory_id, user_id)
            
            # Delete from graph store
            graph_result = self._delete_from_graph_db(memory_id, user_id)
            
            return {
                "success": True,
                "vector_result": vector_result,
                "graph_result": graph_result
            }
        except Exception as e:
            logger.error(f"Error deleting memory: {str(e)}")
            return {"success": False, "error": str(e)}

    # Helper methods for vector store operations
    def _store_in_vector_db(self, content, embedding, user_id, metadata):
        # Implementation for storing in vector database
        pass

    def _search_vector_db(self, query_embedding, user_id, limit):
        # Implementation for searching vector database
        pass

    def _delete_from_vector_db(self, memory_id, user_id):
        # Implementation for deleting from vector database
        pass

    # Helper methods for graph store operations
    def _store_in_graph_db(self, content, user_id, metadata):
        # Implementation for storing in graph database
        pass

    def _search_graph_db(self, query, user_id, limit):
        # Implementation for searching graph database
        pass

    def _delete_from_graph_db(self, memory_id, user_id):
        # Implementation for deleting from graph database
        pass

    def _merge_search_results(self, vector_results, graph_results):
        # Implementation for merging and ranking results
        pass