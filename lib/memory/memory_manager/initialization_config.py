from typing import Dict
from langchain.llms import GoogleGenerativeAI
from langchain.embeddings import JinaEmbeddings
from langchain.vectorstores import Milvus
from mem0.memory.main import Memory as Mem0Memory

class InitializationConfig:
    def __init__(self, config: Dict):
        self.config = config
        self.llm = self._init_llm()
        self.embeddings = self._init_embeddings()
        self.vector_store = self._init_vector_store()
        self.mem0 = self._init_mem0()
        
    def _init_llm(self):
        return GoogleGenerativeAI(
            model=self.config.get("model_name", "gemini-pro"),
            google_api_key=self.config["google_api_key"]
        )
    
    def _init_embeddings(self):
        return JinaEmbeddings(
            api_key=self.config["jina_api_key"]
        )
    
    def _init_vector_store(self):
        return Milvus(
            connection_args=self.config["milvus_config"],
            embedding_function=self.embeddings
        )
        
    def _init_mem0(self):
        return Mem0Memory(config=self.config)