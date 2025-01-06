const DEFAULT_CONFIG = {
    milvus: {
        url: "http://localhost:19530",
        collection_name: "mem0",
        embedding_model_dims: 1536,
        metric_type: "L2"
    },
    neo4j: {
        url: "bolt://localhost:7687",
        username: "neo4j",
        password: "password"
    },
    llm: {
        model_name: "google/gemini-pro",
        temperature: 0.7
    },
    embeddings: {
        model_name: "jina-embeddings-v2"
    }
}