# memory_manager.py
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from langchain_google_genai import GoogleGenerativeAI
from langchain_community.embeddings import JinaEmbeddings
from langchain_community.vectorstores import Milvus
from langchain_community.graphs import Neo4jGraph
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate
import json

logger = logging.getLogger(__name__)

class EnhancedMemoryManager:
    def __init__(self, config: Dict):
        """Initialize the EnhancedMemoryManager with configuration"""
        self._validate_config(config)
        self.config = config
        self.initialize_components()
        asyncio.create_task(self.connect())

    def _validate_config(self, config: Dict) -> None:
        """Validate configuration parameters"""
        required_keys = {
            "llm": ["model_name", "api_key", "temperature"],
            "embeddings": ["api_key", "model_name"],
            "milvus": ["host", "port", "collection_name"],
            "neo4j": ["url", "username", "password"]
        }
        
        for section, keys in required_keys.items():
            if section not in config:
                raise ValueError(f"Missing configuration section: {section}")
            for key in keys:
                if key not in config[section]:
                    raise ValueError(f"Missing configuration key: {section}.{key}")

    async def connect(self) -> None:
        """Establish connections to databases"""
        try:
            # Connect to Milvus
            await self.vector_store.connect()
            
            # Verify Neo4j connection
            with self.graph.driver.session() as session:
                session.run("MATCH (n) RETURN count(n) LIMIT 1")
                
            logger.info("Successfully connected to all databases")
        except Exception as e:
            logger.error(f"Failed to connect to databases: {str(e)}")
            raise

    async def disconnect(self) -> None:
        """Close database connections"""
        try:
            await self.vector_store.disconnect()
            self.graph.driver.close()
        except Exception as e:
            logger.error(f"Error disconnecting: {str(e)}")

    def initialize_components(self) -> None:
        """Initialize all required components with enhanced error handling"""
        try:
            # Initialize Google Generative AI
            self.llm = GoogleGenerativeAI(
                model=self.config["llm"]["model_name"],
                google_api_key=self.config["llm"]["api_key"],
                temperature=self.config["llm"]["temperature"]
            )

            # Initialize Jina Embeddings
            self.embeddings = JinaEmbeddings(
                jina_api_key=self.config["embeddings"]["api_key"],
                model_name=self.config["embeddings"]["model_name"]
            )

            # Initialize Milvus Vector Store
            self.vector_store = Milvus(
                embedding_function=self.embeddings,
                connection_args={
                    "host": self.config["milvus"]["host"],
                    "port": self.config["milvus"]["port"],
                    "collection_name": self.config["milvus"]["collection_name"]
                }
            )

            # Initialize Neo4j Graph
            self.graph = Neo4jGraph(
                url=self.config["neo4j"]["url"],
                username=self.config["neo4j"]["username"],
                password=self.config["neo4j"]["password"]
            )

            # Initialize Conversation Memory
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )

            # Initialize Conversation Chain
            self.conversation = ConversationChain(
                llm=self.llm,
                memory=self.memory,
                verbose=True
            )
            
            logger.info("Successfully initialized all components")
        except Exception as e:
            logger.error(f"Error initializing components: {str(e)}")
            raise

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
            # Get vector store stats
            vector_count = await self.vector_store.count(
                filter=f"metadata.user_id = '{user_id}'"
            )
            
            # Get Neo4j stats
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
            # Check vector store
            await self.vector_store.ping()
            status["vector_store"] = True
            
            # Check Neo4j
            with self.graph.driver.session() as session:
                session.run("RETURN 1")
                status["graph_db"] = True
                
            # Check LLM
            await self.llm.agenerate([ChatPromptTemplate.from_messages([("user", "test")])])
            status["llm"] = True
            
            # Check embeddings
            self.embeddings.embed_query("test")
            status["embeddings"] = True
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            
        return status

    def _process_entities(self, entities_text: str) -> List[Dict]:
        """Process and validate extracted entities"""
        try:
            # Convert string representation to Python object
            if isinstance(entities_text, str):
                import ast
                entities = ast.literal_eval(entities_text)
            else:
                entities = entities_text
                
            # Validate entity format
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

      async def add_memory(self, content: str, user_id: str, metadata: Optional[Dict] = None) -> Dict:
        """Add new memory entry"""
        try:
            # Add timestamp if not provided
            metadata = metadata or {}
            if "timestamp" not in metadata:
                metadata["timestamp"] = datetime.now().isoformat()

            # Generate embeddings and store in Milvus
            vector_id = await self._store_in_vector_db(content, user_id, metadata)

            # Store in Neo4j graph with relationships
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

    async def search_memories(self, query: str, user_id: str, limit: int = 5) -> List[Dict]:
        """Search for relevant memories"""
        try:
            # Search vector store
            vector_results = await self._search_vector_store(query, limit)

            # Search graph database
            graph_results = await self._search_graph_db(query, user_id)

            # Combine and rank results
            combined_results = self._merge_and_rank_results(vector_results, graph_results)

            return combined_results
        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            raise

    async def _store_in_vector_db(self, content: str, user_id: str, metadata: Optional[Dict]) -> str:
        """Store content in Milvus vector store"""
        try:
            metadata = metadata or {}
            metadata["user_id"] = user_id
            
            doc_id = self.vector_store.add_texts(
                texts=[content],
                metadatas=[metadata]
            )[0]
            
            return doc_id
        except Exception as e:
            logger.error(f"Error storing in vector DB: {str(e)}")
            raise

    async def _store_in_graph_db(self, content: str, user_id: str, metadata: Optional[Dict]) -> str:
        """Store content in Neo4j graph database"""
        try:
            # Extract entities and relationships using LLM
            entities = await self._extract_entities(content)
            
            # Create Neo4j query
            query = """
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
            
            result = self.graph.query(
                query,
                params={
                    "content": content,
                    "user_id": user_id,
                    "timestamp": metadata.get("timestamp", datetime.now().isoformat()),
                    "entities": entities
                }
            )
            
            return result[0]["memory_id"]
        except Exception as e:
            logger.error(f"Error storing in graph DB: {str(e)}")
            raise

    async def _search_vector_store(self, query: str, limit: int) -> List[Dict]:
        """Search Milvus vector store"""
        try:
            results = self.vector_store.similarity_search_with_score(
                query=query,
                k=limit
            )
            
            return [
                {
                    "content": result[0].page_content,
                    "metadata": result[0].metadata,
                    "score": result[1]
                }
                for result in results
            ]
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            raise

    async def _search_graph_db(self, query: str, user_id: str) -> List[Dict]:
        """Search Neo4j graph database"""
        try:
            # Extract entities from query
            query_entities = await self._extract_entities(query)
            
            # Create Neo4j search query
            search_query = """
            MATCH (m:Memory {user_id: $user_id})-[:CONTAINS]->(e:Entity)
            WHERE e.name IN $entity_names
            WITH m, collect(e.name) as entities
            RETURN m.content as content, 
                   m.timestamp as timestamp,
                   entities,
                   size(entities) as relevance_score
            ORDER BY relevance_score DESC
            """
            
            results = self.graph.query(
                search_query,
                params={
                    "user_id": user_id,
                    "entity_names": [e["name"] for e in query_entities]
                }
            )
            
            return [
                {
                    "content": record["content"],
                    "timestamp": record["timestamp"],
                    "entities": record["entities"],
                    "score": record["relevance_score"]
                }
                for record in results
            ]
        except Exception as e:
            logger.error(f"Error searching graph DB: {str(e)}")
            raise

    async def _extract_entities(self, content: str) -> List[Dict]:
        """Extract entities using Google Generative AI"""
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", "Extract key entities from the following text. Return as a list of dictionaries with 'name' and 'type' keys."),
                ("user", content)
            ])
            
            response = await self.llm.agenerate([prompt.format_messages()])
            entities = response.generations[0][0].text
            
            # Process and validate entities
            return self._process_entities(entities)
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            raise

    def _merge_and_rank_results(self, vector_results: List[Dict], graph_results: List[Dict]) -> List[Dict]:
        """Merge and rank results from both stores"""
        try:
            # Combine results with scoring
            combined_results = []
            
            # Process vector results
            for vr in vector_results:
                combined_results.append({
                    "content": vr["content"],
                    "source": "vector",
                    "score": vr["score"],
                    "metadata": vr["metadata"],
                    "timestamp": vr["metadata"].get("timestamp", "")
                })
            
            # Process graph results
            for gr in graph_results:
                combined_results.append({
                    "content": gr["content"],
                    "source": "graph",
                    "entities": gr["entities"],
                    "score": gr["score"] / 10,  # Normalize graph scores
                    "timestamp": gr["timestamp"]
                })
            
            # Sort by score and timestamp
            combined_results.sort(
                key=lambda x: (x["score"], x["timestamp"]), 
                reverse=True
            )
            
            return combined_results
        except Exception as e:
            logger.error(f"Error merging results: {str(e)}")
            raise
