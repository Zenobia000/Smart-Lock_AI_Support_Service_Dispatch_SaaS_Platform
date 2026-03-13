from .ollama_embed import build_ollama_embedding

# 註冊表：將字串對應到對應的建造函數
REGISTRY = {
    "ollama": build_ollama_embedding,
    # "openai": build_openai_embedding,  # 未來擴充時把這行註解打開即可
}

def get_embedding(config: dict = None):
    # 若 config 未帶 embedding_provider，fallback 至全域 EMBEDDING_CONFIG
    if not config or not config.get("embedding_provider"):
        from core.config import EMBEDDING_CONFIG
        cfg = {
            "embedding_provider": EMBEDDING_CONFIG.get("provider", "ollama"),
            "embedding_model": EMBEDDING_CONFIG.get("model", "nomic-embed-text"),
            "embedding_base_url": EMBEDDING_CONFIG.get("base_url", "http://localhost:11434"),
            "embedding_base_url_env": EMBEDDING_CONFIG.get("base_url_env", "OLLAMA_BASE_URL"),
        }
    else:
        cfg = config

    provider = cfg.get("embedding_provider", "ollama")
    builder = REGISTRY.get(provider)

    if not builder:
        raise ValueError(f"未知的 Embedding 供應商: {provider}，請確認是否已在 embeddings/__init__.py 註冊")

    return builder(cfg)