import os
from langchain_google_genai import ChatGoogleGenerativeAI

def build_vertexai_llm(config: dict):
    model_name = config.get("model_name", "gemini-2.5-flash")
    temperature = config.get("temperature", 0.7)

    project_env = config.get("project_id_env", "VERTEX_PROJECT_ID")
    location_env = config.get("location_env", "VERTEX_LOCATION")

    project_id = os.getenv(project_env)
    location = os.getenv(location_env)

    if not project_id:
        raise ValueError(f"缺少 GCP 專案 ID！請在 .env 檔案中設定 {project_env}")

    if not location:
        raise ValueError(f"缺少 GCP 區域！請在 .env 檔案中設定 {location_env}")

    return ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
        project=project_id,
        location=location,
        vertexai=True,
    )
