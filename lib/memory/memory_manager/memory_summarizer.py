import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class MemorySummarizer:
    def __init__(self, llm):
        self.llm = llm
        
    async def summarize_memories(self, memories: List[Dict]) -> Dict:
        """
        Summarizes a collection of memories into a condensed format
        """
        try:
            summary_prompt = """
            Summarize the following memories while preserving key information:
            {memories}
            
            Provide a concise summary that captures:
            1. Main topics/themes
            2. Key entities and relationships
            3. Important temporal information
            """
            
            formatted_memories = "\n".join([str(m) for m in memories])
            
            summary = await self.llm.generate_response(
                messages=[
                    {"role": "system", "content": summary_prompt},
                    {"role": "user", "content": formatted_memories}
                ]
            )
            
            return {
                "original_count": len(memories),
                "summary": summary,
                "timestamp": self._get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error in memory summarization: {str(e)}")
            return None
            
    def _get_current_timestamp(self):
        from datetime import datetime
        return datetime.utcnow().isoformat()