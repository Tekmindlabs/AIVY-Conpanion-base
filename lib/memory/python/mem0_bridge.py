# mem0_bridge.py
import os
import json
import logging
import sys
import google.generativeai as genai
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Mem0Bridge:
    def __init__(self):
        """Initialize the Mem0Bridge with configuration and memory system."""
        try:
            # Check required environment variables
            required_env_vars = [
                "MILVUS_URL",
                "MILVUS_TOKEN",
                "NEO4J_URL",
                "NEO4J_USER",
                "NEO4J_PASSWORD",
                "GOOGLE_API_KEY"
            ]
            
            missing_vars = [var for var in required_env_vars if not os.getenv(var)]
            if missing_vars:
                raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

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
            logger.debug(f"Memory added successfully: {result}")
            return result
        except Exception as e:
            error_msg = f"Error adding memory: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def search_memories(self, query: str, user_id: str, limit: int = 10) -> Dict:
        """Search memories based on query."""
        try:
            results = self.memory.search(
                query=query,
                user_id=user_id,
                limit=limit
            )
            logger.debug(f"Search completed successfully: {len(results)} results found")
            return {"success": True, "results": results}
        except Exception as e:
            error_msg = f"Error searching memories: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def delete_memory(self, memory_id: str, user_id: str) -> Dict:
        """Delete a specific memory."""
        try:
            result = self.memory.delete(memory_id=memory_id, user_id=user_id)
            logger.debug(f"Memory deleted successfully: {result}")
            return {"success": True, "result": result}
        except Exception as e:
            error_msg = f"Error deleting memory: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

# [Previous Memory class implementation remains the same]
# ... (Keep the existing Memory class implementation)

if __name__ == "__main__":
    logger.debug(f"Script started with arguments: {sys.argv}")
    
    if len(sys.argv) < 3:
        error_result = {"error": "Insufficient arguments"}
        print(json.dumps(error_result))
        sys.exit(1)

    command = sys.argv[1]
    try:
        args = json.loads(sys.argv[2])
        logger.debug(f"Parsed command: {command}, args: {args}")
        
        bridge = Mem0Bridge()
        
        if command == "add":
            result = bridge.add_memory(args["content"], args["userId"], args.get("metadata"))
            print(json.dumps(result))
        elif command == "search":
            result = bridge.search_memories(args["query"], args["userId"], args.get("limit", 10))
            print(json.dumps(result))
        elif command == "delete":
            result = bridge.delete_memory(args["memoryId"], args["userId"])
            print(json.dumps(result))
        else:
            error_result = {"error": f"Unknown command: {command}"}
            print(json.dumps(error_result))
            
    except json.JSONDecodeError as e:
        error_result = {"error": f"Invalid JSON arguments: {str(e)}"}
        print(json.dumps(error_result))
    except Exception as e:
        error_result = {"error": str(e)}
        print(json.dumps(error_result))