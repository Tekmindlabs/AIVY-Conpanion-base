# mem0_bridge.py

import os
import json
import logging
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from pymilvus import connections, Collection, utility
from neo4j import GraphDatabase

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Memory:
    def __init__(self, config):
        """Initialize Memory with configuration."""
        self.config = config
        
        # Initialize Milvus
        connections.connect(
            alias="default",
            uri=config["vector_store"]["config"]["url"],
            token=config["vector_store"]["config"]["token"]
        )
        
        # Initialize Neo4j
        self.neo4j_driver = GraphDatabase.driver(
            config["graph_store"]["config"]["url"],
            auth=(
                config["graph_store"]["config"]["username"],
                config["graph_store"]["config"]["password"]
            )
        )
        
        # Initialize Google AI
        genai.configure(api_key=config["llm"]["config"]["api_key"])
        self.model = genai.GenerativeModel(config["llm"]["config"]["model"])

    def add(self, messages: List[Dict], user_id: str, metadata: Optional[Dict] = None) -> Dict:
        """Add a new memory."""
        try:
            # Create collection if it doesn't exist
            collection_name = self.config["vector_store"]["config"]["collection_name"]
            if not utility.has_collection(collection_name):
                # Initialize collection with proper schema
                # (Add your collection creation logic here)
                pass
                
            collection = Collection(collection_name)
            
            # Process messages and create embeddings
            content = " ".join([msg["content"] for msg in messages])
            embedding = self._create_embedding(content)
            
            # Store in Milvus
            memory_id = self._store_in_milvus(collection, embedding, content, user_id, metadata)
            
            # Store in Neo4j
            self._store_in_neo4j(memory_id, user_id, content, metadata)
            
            return {
                "success": True,
                "memory_id": memory_id,
                "user_id": user_id,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error adding memory: {str(e)}")
            return {"success": False, "error": str(e)}

    def search(self, query: str, user_id: str, limit: int = 10) -> List[Dict]:
        """Search for memories."""
        try:
            collection = Collection(self.config["vector_store"]["config"]["collection_name"])
            
            # Create query embedding
            query_embedding = self._create_embedding(query)
            
            # Search in Milvus
            search_params = {
                "metric_type": self.config["vector_store"]["config"]["metric_type"],
                "params": {"nprobe": 10},
            }
            
            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=limit,
                expr=f'user_id == "{user_id}"'
            )
            
            # Format results
            memories = []
            for hits in results:
                for hit in hits:
                    memories.append({
                        "id": hit.id,
                        "content": hit.entity.get("content"),
                        "score": hit.score,
                        "metadata": hit.entity.get("metadata", {})
                    })
                    
            return memories
            
        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            return []

    def delete(self, memory_id: str, user_id: str) -> Dict:
        """Delete a memory."""
        try:
            # Delete from Milvus
            collection = Collection(self.config["vector_store"]["config"]["collection_name"])
            collection.delete(f'memory_id == "{memory_id}" && user_id == "{user_id}"')
            
            # Delete from Neo4j
            with self.neo4j_driver.session() as session:
                session.run(
                    "MATCH (m:Memory {id: $memory_id, user_id: $user_id}) "
                    "DETACH DELETE m",
                    memory_id=memory_id,
                    user_id=user_id
                )
                
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Error deleting memory: {str(e)}")
            return {"success": False, "error": str(e)}

    def _create_embedding(self, text: str) -> List[float]:
        """Create embedding using Google AI."""
        response = self.model.embed_content(text=text)
        return response.embedding

    def _store_in_milvus(self, collection, embedding, content, user_id, metadata):
        """Store memory in Milvus."""
        memory_id = str(uuid.uuid4())
        collection.insert([{
            "memory_id": memory_id,
            "user_id": user_id,
            "content": content,
            "embedding": embedding,
            "metadata": metadata
        }])
        return memory_id

    def _store_in_neo4j(self, memory_id, user_id, content, metadata):
        """Store memory in Neo4j."""
        with self.neo4j_driver.session() as session:
            session.run(
                "CREATE (m:Memory {id: $memory_id, user_id: $user_id, "
                "content: $content, metadata: $metadata})",
                memory_id=memory_id,
                user_id=user_id,
                content=content,
                metadata=metadata
            )
