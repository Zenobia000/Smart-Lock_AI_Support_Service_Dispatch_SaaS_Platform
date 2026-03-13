from .ollama_model import build_ollama_llm
from .gemini_model import build_gemini_llm
from .vertexai_model import build_vertexai_llm

LLM_REGISTRY = {
    "ollama": build_ollama_llm,
    "gemini": build_gemini_llm,
    "vertexai": build_vertexai_llm,
}

def get_llm(llm_config: dict):
    provider = llm_config.get("provider", "ollama")
    builder = LLM_REGISTRY.get(provider)
    
    if not builder:
        raise ValueError(f"未知的 LLM 供應商: {provider}，請確認是否已註冊。")

    model_name = llm_config.get("model_name", "未指定")
    print(f"[*] 初始化 LLM: 載入 {provider} (模型: {model_name})")

    return builder(llm_config)