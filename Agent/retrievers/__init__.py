from .chroma_store import ChromaRetriever
from .api_store import APIStoreRetriever
from .web_search import WebSearchRetriever

REGISTRY = {
    "chroma": ChromaRetriever,
    "api": APIStoreRetriever,
    "web_search": WebSearchRetriever,
}

def get_retriever(db_config: dict):
    db_type = db_config.get("type")
    retriever_class = REGISTRY.get(db_type)
    
    if not retriever_class:
        raise ValueError(f"未知的資料庫類型: {db_type}，請確認是否已在 retrievers/__init__.py 註冊")
    
    return retriever_class(db_config)