import os
from langchain_ollama import ChatOllama

def build_ollama_llm(config: dict):
    model_name = config.get("model_name", "gemma3:4b")
    temperature = config.get("temperature", 0.7)
    
    env_url_name = config.get("base_url_env", "OLLAMA_BASE_URL")
    base_url = os.getenv(env_url_name) or config.get("base_url", "http://localhost:11434")
    
    print(f"[*] 初始化 LLM: 載入本地 Ollama (模型: {model_name}, 網址: {base_url})")
    
    return ChatOllama(
        model=model_name, 
        temperature=temperature,
        base_url=base_url
    )