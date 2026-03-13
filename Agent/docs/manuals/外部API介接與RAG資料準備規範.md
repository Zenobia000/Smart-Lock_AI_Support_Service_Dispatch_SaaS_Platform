# 外部 API 介接與 RAG 資料準備規範

本文件旨在指導開發者如何擴充系統的知識來源，包含 RAG 向量庫的更新與 RESTful API 的整合。

---

## 1. RAG 知識庫資料準備 (Vector DB)

系統目前的示範資料直接定義於 `scripts/seed_db.py` 腳本中。執行該腳本會將內建的 Document 物件寫入 ChromaDB 向量庫。

### 1.1 資料內容規範
*   **目前位置**：資料定義在 `scripts/seed_db.py` 的 `manual_docs`（產品手冊）與 `troubleshooting_docs`（故障排除）清單中。
*   **內容結構**：每份 Document 應專注於單一主題（例如「Philips Alpha 指紋設定步驟」）。
*   **中繼資料 (Metadata)**：建議包含 brand（品牌）、model（型號）與 source（來源檔案名稱）等欄位，這有助於 Embedding 捕捉關聯性並讓 Agent 進行精準過濾。

### 1.2 資料分割 (Chunking) 建議
*   目前示範資料採手動切分好的 Document 物件。
*   若未來擴充為讀取外部檔案，建議使用 `RecursiveCharacterTextSplitter`。
*   建議 `chunk_size` 設為 500 字，`chunk_overlap` 設為 50 字。

### 1.3 更新知識庫流程
1.  修改 `scripts/seed_db.py` 中的 `manual_docs` 或 `troubleshooting_docs` 列表，加入新的 Document 物件。
2.  執行腳本：`python scripts/seed_db.py`。
3.  該腳本會自動根據 `config.toml` 中的 `[[databases]]` 路徑清理舊資料並重建索引。

---

## 2. 外部 API 介接 (API Store)

### 2.1 對接現有架構
若要將 `order_clerk` Agent 接到真實的後台：
1.  **修改 `.env`**：填入真實的 `ORDER_API_URL` 與 `ORDER_API_TOKEN`。
2.  **修改 `config.toml`**：
    ```toml
    [[databases]]
    name = "db_order_api"
    type = "api"
    # ...
    query_param = "keyword"      # 發送時的參數名
    response_key = "message"     # JSON 中要擷取的結果欄位
    ```

### 2.2 API 回傳要求
*   **格式**：必須回傳 JSON。
*   **效能**：超時應控制在 5 秒內（`timeout` 參數）。
*   **內容**：回傳內容應包含關鍵資訊（如：訂單狀態、物流單號、預計到貨時間），以便 Agent 生成回覆。

---

## 3. 嵌入模型切換 (Embeddings)

目前的預設模型是 Ollama 的 `nomic-embed-text`。若需切換至更高精度的模型（如 OpenAI 或 Vertex AI）：
1.  **新增 Embedding Provider**：參考 `docs/系統擴充開發指南.md` 實作新的 provider。
2.  **更新設定**：在 `config.toml` 中將對應 `[[databases]]` 的 `embedding_provider` 欄位進行修改。
3.  **注意**：更換 Embedding 模型後，**必須**重新建立所有向量資料庫，否則會出現向量維度不匹配的錯誤。
