import logging
from typing import List, Dict, Optional
from langchain.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

class SearchProcessing:
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
        """Extract entities using LLM"""
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", "Extract key entities from the following text. Return as a list of dictionaries with 'name' and 'type' keys."),
                ("user", content)
            ])
            
            response = await self.llm.agenerate([prompt.format_messages()])
            entities = response.generations[0][0].text
            
            return self._process_entities(entities)
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            raise

    def _merge_and_rank_results(self, vector_results: List[Dict], graph_results: List[Dict]) -> List[Dict]:
        """Merge and rank results from both stores"""
        try:
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