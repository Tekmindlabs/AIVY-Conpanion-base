import logging
from typing import Dict
from langchain_google_genai import GoogleGenerativeAI
from langchain_community.embeddings import JinaEmbeddings
from langchain_community.vectorstores import Milvus
from langchain_community.graphs import Neo4jGraph
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

logger = logging.getLogger(__name__)

class InitializationConfig:
    def __init__(self, config: Dict):
        self._validate_config(config)
        self.config = config
        self.initialize_components()
        
    def _validate_config(self, config: Dict) -> None:
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

    def initialize_components(self) -> None:
        """Initialize all required components"""
        try:
            self.llm = GoogleGenerativeAI(
                model=self.config["llm"]["model_name"],
                google_api_key=self.config["llm"]["api_key"],
                temperature=self.config["llm"]["temperature"]
            )

            self.embeddings = JinaEmbeddings(
                jina_api_key=self.config["embeddings"]["api_key"],
                model_name=self.config["embeddings"]["model_name"]
            )

            self.vector_store = Milvus(
                embedding_function=self.embeddings,
                connection_args={
                    "host": self.config["milvus"]["host"],
                    "port": self.config["milvus"]["port"],
                    "collection_name": self.config["milvus"]["collection_name"]
                }
            )

            self.graph = Neo4jGraph(
                url=self.config["neo4j"]["url"],
                username=self.config["neo4j"]["username"],
                password=self.config["neo4j"]["password"]
            )

            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )

            self.conversation = ConversationChain(
                llm=self.llm,
                memory=self.memory,
                verbose=True
            )
            
            logger.info("Successfully initialized all components")
        except Exception as e:
            logger.error(f"Error initializing components: {str(e)}")
            raise