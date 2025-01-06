# config.py
DEFAULT_CONFIG = {
    "llm": {
        "provider": "google",
        "model_name": "gemini-pro",
        "api_key": "your_google_api_key",
        "temperature": 0.7
    },
    "embeddings": {
        "provider": "jina",
        "api_key": "your_jina_api_key",
        "model_name": "jina-embeddings-v2"
    },
    "milvus": {
        "host": "localhost",
        "port": 19530,
        "collection_name": "memories"
    },
    "neo4j": {
        "url": "bolt://localhost:7687",
        "username": "neo4j",
        "password": "your_password"
    }
}