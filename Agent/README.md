# Smart Lock AI Agent

智慧電子鎖客服聊天機器人，基於 **LangGraph** 建構 RAG 檢索增強生成管線，透過 **LINE Bot** (FastAPI webhook) 對外服務。

## 功能特色

- **零硬編碼設定驅動**：所有行為參數、Prompt 路徑、Regex 均由 `config.toml` 控制，13 個區塊涵蓋系統全貌，無需改 Python 即可擴充
- **雙軌持久化日誌**：`chat_history.db`（對話記憶 + 語意摘要壓縮）與 `audit_log.db`（原始日誌審計），各自獨立運作
- **插件式架構**：LLM / Retriever / Embedding / Storage 均透過 Registry 工廠模式熱切換，新增供應商只需註冊一行
- **多 Agent 架構**：Router 意圖分類 → 專職 Agent 子圖（product_expert / troubleshooter / order_clerk / web_researcher）
- **多意圖平行派發**：Send() fan-out，一則訊息可同時觸發多個 Agent 並行處理
- **自主解決優先**：Agent 竭盡所能自主解決，僅在使用者明確堅持或涉及安全風險時轉接真人
- **對話記憶**：SQLite 持久化 + 語意摘要壓縮（manage_memory），跨 session 不遺失
- **使用者輪廓**：自動萃取並持久化使用者設備、地址、電話等個資
- **審計日誌**：即時記錄原始訊息（user_raw）+ 合併訊息（user）+ AI 回覆（ai），完整審計軌跡
- **訊息防抖**：LINE 訊息緩衝合併，計時器重設機制避免碎片化處理

## 系統架構

```
START → pre_process → manage_memory → router →  product_expert  ─┐
                                             →  troubleshooter   ─┤
                                             →  order_clerk       ─┤→ merge_answers → update_profile → post_process → END
                                             →  web_researcher   ─┤
                                             →  out_of_domain     ─┤
                                             →  transfer_human    ─┘
```

## 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 設定環境變數

複製 `.env.example`（或自行建立 `.env`），填入必要的金鑰：

```env
# LINE Bot（必要）
LINE_CHANNEL_SECRET="your-line-channel-secret"
LINE_CHANNEL_ACCESS_TOKEN="your-line-channel-access-token"

# LLM — 依 config.toml [llm].provider 選擇
GEMINI_API_KEY="your-gemini-api-key"        # provider=gemini 時必要
VERTEX_PROJECT_ID="your-gcp-project-id"     # provider=vertexai 時必要
VERTEX_LOCATION="us-central1"               # provider=vertexai 時必要
OLLAMA_BASE_URL="http://localhost:11434"    # 選填，預設 http://localhost:11434

# 外部 API（選填）
ORDER_API_URL="https://api.example.com/v1/status"
ORDER_API_TOKEN="your-bearer-token"

# PostgreSQL（選填，memory/storage type=postgres 時必要）
POSTGRES_URI="postgresql://user:pass@host:5432/dbname"
```

### 3. 建立向量資料庫

```bash
python scripts/seed_db.py
```

### 4. 執行

```bash
# CLI 測試模式
python main.py

# LINE Bot webhook 伺服器
uvicorn app:app --reload
```

## 其他指令

```bash
# Mock 訂單 API（測試用）
uvicorn scripts.mock_api:app --port 8001

# 查看審計日誌
python scripts/view_logs.py

# 執行測試
python -m pytest tests/test_debounce.py
```

## LLM 供應商

透過 `config.toml` 的 `[llm].provider` 切換：

| Provider | 說明 | 驗證方式 |
| :--- | :--- | :--- |
| `ollama` | 本地 / 遠端 Ollama | 無需金鑰 |
| `gemini` | Google Gemini API | `GEMINI_API_KEY` |
| `vertexai` | Google Vertex AI | ADC (`gcloud auth application-default login`) |

## 專案結構

```
lock_AI_Agent/
├── app.py                  # LINE Bot FastAPI webhook（含防抖層與審計日誌）
├── main.py                 # CLI 測試入口
├── config.toml             # 系統設定檔（13 個區塊，零硬編碼）
├── core/                   # 核心模組
│   ├── config.py           # TOML 解析 → 13 個 Python 設定變數
│   └── constants.py        # 共用常數（PHONE_REGEX / ADDRESS_REGEX，從 config 動態載入）
├── graph/                  # LangGraph 管線
│   ├── state.py            # GraphState TypedDict
│   ├── nodes.py            # 節點邏輯（8 個節點函數）
│   └── builder.py          # StateGraph 組裝 + Send() fan-out
├── agents/                 # 多 Agent 架構
│   ├── __init__.py         # build_agent_executor / build_all_agents
│   └── prompts/            # 提示詞模板（9 個 .md 檔案）
├── tools/                  # 工具建構（Retriever 包裝 + transfer_to_human）
├── llms/                   # LLM 工廠（ollama / gemini / vertexai）
├── embeddings/             # Embedding 工廠
├── retrievers/             # 檢索器工廠（chroma / api / web_search）
├── memory/                 # 對話記憶 Checkpointer（memory / sqlite / postgres）
├── profiles/               # 使用者輪廓管理（Markdown 持久化）
├── storage/                # 審計日誌工廠（sqlite / postgres）
├── scripts/                # 輔助腳本（seed_db / mock_api / view_logs）
├── data/                   # 動態資料（gitignore）
│   ├── db/                 # chat_history.db + audit_log.db + chroma_db_*
│   └── profiles/           # 使用者輪廓 *.md
├── docs/                   # 文件
│   ├── manuals/            # 系統指南（7 份手冊）
│   ├── reports/            # 進度報告
│   └── assets/             # 架構圖（.mmd / .png）
└── tests/                  # 測試
```
