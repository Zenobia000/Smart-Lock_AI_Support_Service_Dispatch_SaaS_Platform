import os
from langchain_chroma import Chroma
from .base import BaseRetriever

from embeddings import get_embedding 

class ChromaRetriever(BaseRetriever):
    def setup(self):
        db_path = self.config.get("path", "./data/db/chroma_db_default")
        self.top_k = self.config.get("top_k", 2)

        embed_fn = get_embedding(self.config)
        
        print(f"[*] 初始化 Async ChromaDB: 連線至資料庫路徑 {db_path}...")
            
        self.vector_store = Chroma(
            persist_directory=db_path, 
            embedding_function=embed_fn
        )

    async def aretrieve(self, question: str) -> str:
        docs = await self.vector_store.asimilarity_search(question, k=self.top_k)
        context = "\n---\n".join([doc.page_content for doc in docs])
        return context if context else "此資料庫查無相關文件。"