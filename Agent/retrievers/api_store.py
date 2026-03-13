import os
import httpx
from .base import BaseRetriever

class APIStoreRetriever(BaseRetriever):
    def setup(self):
        env_url_name = self.config.get("endpoint_env")
        self.endpoint = os.getenv(env_url_name) or self.config.get("endpoint")
        
        env_token_name = self.config.get("token_env")
        self.api_token = os.getenv(env_token_name)

        self.method = self.config.get("method", "GET").upper()
        self.timeout = self.config.get("timeout", 5)
        self.query_param = self.config.get("query_param", "q")
        self.response_key = self.config.get("response_key", "data")
        
        print(f"[*] 初始化 Async API 模組: 準備連線至 {self.endpoint} ...")

    async def aretrieve(self, question: str) -> str:
        headers = {}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if self.method == "GET":
                    response = await client.get(self.endpoint, params={self.query_param: question}, headers=headers)
                elif self.method == "POST":
                    response = await client.post(self.endpoint, json={self.query_param: question}, headers=headers)
                else:
                    return f"不支援的 HTTP 方法: {self.method}"

                response.raise_for_status()
                data = response.json()
                context = data.get(self.response_key, "API 呼叫成功，但找不到指定的內容欄位。")
                return str(context)

        except httpx.TimeoutException:
            return "API 請求超時，無法取得資料。"
        except httpx.RequestError as e:
            return f"API 連線發生錯誤: {e}"
        except Exception as e:
            return f"API 解析發生異常: {e}"
            