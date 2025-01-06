# memory_manager.py
import logging
from typing import Dict, List, Optional
from langchain_google_genai import GoogleGenerativeAI
from langchain_community.embeddings import JinaEmbeddings
from langchain_community.vectorstores import Milvus
from langchain_community.graphs import Neo4jGraph
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

class EnhancedMemoryManager:
    def __init__(self, config: Dict):
        self.config = config
        self.initialize_components()

    def initialize_components(self):
        """Initialize all required components"""
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

    async def add_memory(self, content: str, user_id: str, metadata: Optional[Dict] = None) -> Dict:
        """Add new memory entry"""
        try:
            # Generate embeddings and store in Milvus
            vector_id = await self._store_in_vector_db(content, user_id, metadata)

            # Store in Neo4j graph with relationships
            graph_id = await self._store_in_graph_db(content, user_id, metadata)

            return {
                "status": "success",
                "vector_id": vector_id,
                "graph_id": graph_id
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
            CREATE (m:Memory {content: $content, user_id: $user_id})
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
            RETURN m.content as content, collect(e.name) as entities
            """
            
            results = self.graph.query(
                search_query,
                params={
                    "user_id": user_id,
                    "entity_names": [e["name"] for e in query_entities]
                }
            )
            
            return results
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
                    "metadata": vr["metadata"]
                })
            
            # Process graph results
            for gr in graph_results:
                combined_results.append({
                    "content": gr["content"],
                    "source": "graph",
                    "entities": gr["entities"],
                    "score": len(gr["entities"]) / 10  # Simplified scoring
                })
            
            # Sort by score
            combined_results.sort(key=lambda x: x["score"], reverse=True)
            
            return combined_results
        except Exception as e:
            logger.error(f"Error merging results: {str(e)}")
            raise