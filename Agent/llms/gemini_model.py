import os
from langchain_google_genai import ChatGoogleGenerativeAI

def build_gemini_llm(config: dict):
    model_name = config.get("model_name", "gemini-2.5-flash")
    temperature = config.get("temperature", 0.7)
    
    env_var_name = config.get("api_key_env", "GEMINI_API_KEY")
    
    api_key = os.getenv(env_var_name)
    
    if not api_key:
        raise ValueError(f"缺少金鑰！請在 .env 檔案中設定 {env_var_name}")
        
    return ChatGoogleGenerativeAI(
        model=model_name, 
        temperature=temperature,
        google_api_key=api_key
    )