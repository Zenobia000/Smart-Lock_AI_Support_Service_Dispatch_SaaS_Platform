# 系統設定檔 (`config.toml`) 說明文件

本文件詳細說明多 Agent RAG 客服系統的核心設定檔 `config.toml` 中各項區塊與參數的意義。

---

## 1. 系統全局設定 `[system]`

定義系統的業務守備範圍（Domain Guardrail）與全域行為參數。Router 與各 Agent 會依此判斷問題是否屬於服務範圍，超出範圍的問題會被導向 `out_of_domain` 節點禮貌拒絕。

```toml
[system]
domain          = "電子鎖、智慧門鎖相關的產品、安裝、故障排除與售後服務"
thread_prefix   = "smart_lock_"    # LangGraph thread ID 前綴
request_timeout = 60               # LangGraph 執行超時秒數
```

| 參數 | 說明 |
|------|------|
| `domain` | 業務範圍描述字串，寫得越清晰，Router 意圖分類的準確率越高 |
| `thread_prefix` | LangGraph thread ID 前綴，格式為 `{prefix}{user_id}` |
| `request_timeout` | LangGraph 單次執行的超時秒數，超時則回覆 `error_timeout` 範本 |

---

## 2. 訊息緩衝設定 `[debounce]`

LINE 使用者常連續發送多則短訊息。防抖層會緩衝這些訊息，等待一段靜默時間後合併送出，避免重複觸發 LangGraph。

```toml
[debounce]
buffer_wait       = 5.0   # 最後一則訊息後等待秒數，新訊息會重設計時器
buffer_ttl        = 300   # 緩衝區存活秒數，超過則強制清理
cleanup_interval  = 60    # 清理過期緩衝區的間隔秒數
```

| 參數 | 說明 |
|------|------|
| `buffer_wait` | 靜默等待秒數（float），建議 1.0 ~ 5.0 |
| `buffer_ttl` | 緩衝區最大存活秒數，超過則強制清理避免記憶體洩漏 |
| `cleanup_interval` | 背景定期清理的間隔秒數 |

---

## 3. LINE Bot 設定 `[line_bot]`

控制 LINE Bot 的行為參數。

```toml
[line_bot]
loading_animation_time = 5  # Loading 動畫顯示時間 (秒，必須是 5 的倍數，範圍 5~60)
```

| 參數 | 說明 |
|------|------|
| `loading_animation_time` | 使用者送出訊息後顯示「輸入中」動畫的秒數，必須為 5 的倍數 |

---

## 4. 系統回覆範本 `[templates]`

定義系統層級的罐頭訊息文字。

```toml
[templates]
push_fallback_prefix = "【系統通知】讓您久等了，以下是您的回覆：\n"
error_timeout        = "不好意思，系統處理時間過長，請稍後再試一次。如果問題持續，建議轉接真人客服。"
error_system         = "不好意思，系統大腦剛剛稍微當機了一下，請稍後再試一次！"
error_no_reply       = "抱歉，系統沒有產生回覆。"
```

| 參數 | 說明 |
|------|------|
| `push_fallback_prefix` | 當 Reply Token 過期改用 Push API 時，前綴提示文字 |
| `error_timeout` | LangGraph 執行超時時的回覆訊息 |
| `error_system` | 系統異常（例外）時的回覆訊息 |
| `error_no_reply` | LangGraph 未產生回覆時的 fallback 訊息 |

---

## 5. 核心語言模型設定 `[llm]`

設定系統大腦，驅動 Router 意圖分類、Agent 推理、記憶摘要壓縮、輪廓萃取等所有 LLM 呼叫。透過 LLM Factory（`llms/__init__.py`）動態載入。

```toml
[llm]
provider = "vertexai"               # 支援: "ollama", "gemini", "vertexai"
model_name = "gemini-2.5-flash"     # 模型名稱
temperature = 0.3                   # 創造力指數 (0.0 ~ 1.0，客服情境建議低值)

# [Gemini 專用]
api_key_env = "GEMINI_API_KEY"      # 從 .env 讀取 API Key

# [Ollama 專用]
base_url = "http://localhost:11434"
base_url_env = "OLLAMA_BASE_URL"    # 優先讀取環境變數，為空則使用 base_url

# [Vertex AI 專用] (需先執行 gcloud auth application-default login)
project_id_env = "VERTEX_PROJECT_ID"  # GCP 專案 ID
location_env = "VERTEX_LOCATION"      # GCP 區域 (例: us-central1)
```

| 參數 | 說明 |
|------|------|
| `provider` | LLM 供應商，需對應 `llms/` 目錄下已註冊的 provider |
| `model_name` | 模型名稱，依 provider 不同填入對應值 |
| `temperature` | 生成溫度，0.0 最保守、1.0 最有創意 |
| `api_key_env` | Gemini 專用，指向 `.env` 中的 API Key 變數名 |
| `base_url` | Ollama 專用，本地服務連線網址 |
| `base_url_env` | Ollama 專用，優先從環境變數讀取 |
| `project_id_env` | Vertex AI 專用，GCP 專案 ID 環境變數名 |
| `location_env` | Vertex AI 專用，GCP 區域環境變數名 |

> **`_env` 命名慣例**：帶有 `_env` 後綴的參數代表「環境變數名稱」，實際值由 `.env` 檔案提供，避免機密資訊外洩。

---

## 6. 向量模型設定 `[embedding]`

設定全域 Embedding 引擎，驅動所有向量檢索器（如 ChromaDB）的文字向量化。透過 Embeddings Factory（`embeddings/__init__.py`）動態載入。此為全域設定，所有 `[[databases]]` 中的向量檢索器會自動套用，無需重複定義。

```toml
[embedding]
provider     = "ollama"              # 支援: "ollama"（未來可擴充 "openai" 等）
model        = "nomic-embed-text"    # Embedding 模型名稱
base_url     = "http://localhost:11434"
base_url_env = "OLLAMA_BASE_URL"     # 優先讀取環境變數，若為空則使用 base_url
```

| 參數 | 說明 |
|------|------|
| `provider` | Embedding 供應商，需對應 `embeddings/` 目錄下已註冊的 provider |
| `model` | Embedding 模型名稱，依 provider 不同填入對應值 |
| `base_url` | Ollama 專用，本地服務連線網址 |
| `base_url_env` | Ollama 專用，優先從環境變數讀取 |

> **Fallback 機制**：`get_embedding()` 在未收到帶有 `embedding_provider` 的 config 時，會自動 fallback 至此全域設定。個別 `[[databases]]` 仍可透過 `embedding_provider` 欄位覆蓋（per-database override），但通常不需要。

---

## 7. 知識庫與檢索器設定 `[[databases]]`

定義系統可用的資料來源。每個 `[[databases]]` 區塊代表一個檢索器（Retriever），透過 Retriever Factory（`retrievers/__init__.py`）動態載入。Agent 透過 `tools` 欄位綁定所需的檢索器。

### A. 向量資料庫 (ChromaDB)

結合 Embedding Engine（全域 `[embedding]` 設定），將文字轉為向量進行語意搜尋。

```toml
[[databases]]
name = "db_smartlock_manual"             # 唯一名稱，供 Agent tools 綁定
type = "chroma"                          # 檢索器類型
description = "智能門鎖規格、設定與保固手冊"  # Agent 看到的工具描述
path = "./data/db/chroma_db_default"     # 資料庫本機路徑
top_k = 3                               # 每次檢索取回最相關的幾筆資料
# Embedding 自動使用全域 [embedding] 設定，無需重複定義
```

| 參數 | 說明 |
|------|------|
| `name` | 唯一識別名，Agent 的 `tools` 陣列會引用此名稱 |
| `type` | 檢索器類型，對應 `retrievers/REGISTRY` 中的 key |
| `description` | 工具描述，LLM 據此判斷何時呼叫該工具 |
| `path` | ChromaDB 本機資料夾路徑 |
| `top_k` | 語意搜尋回傳的最相關文件數量 |

> Embedding 模型設定統一在 `[embedding]` 區塊管理，不再於此重複。若需個別覆蓋，可加入 `embedding_provider` 等欄位。

### B. 內部 API 串接 (API Store)

適合查詢即時動態資料（如訂單狀態、維修進度）。

```toml
[[databases]]
name = "db_order_api"
type = "api"
description = "查詢即時訂單狀態與報修進度"

endpoint = "https://api.sunnie-lock.com/v1/status"  # API 端點
endpoint_env = "ORDER_API_URL"     # (優先) 從 .env 讀取真實機密網址
token_env = "ORDER_API_TOKEN"      # (選用) 從 .env 讀取 Bearer Token
method = "GET"                     # HTTP 方法 (GET/POST)
timeout = 5                        # 連線超時 (秒)

query_param = "keyword"            # 查詢參數名 (例: ?keyword=問題)
response_key = "message"           # JSON 回傳中要萃取的欄位
```

| 參數 | 說明 |
|------|------|
| `endpoint` | API 端點 URL |
| `endpoint_env` | 從 `.env` 讀取真實 URL（優先於 `endpoint`） |
| `token_env` | Bearer Token 環境變數名（選用） |
| `method` | HTTP 方法 |
| `timeout` | 連線超時秒數 |
| `query_param` | 使用者問題放入的查詢參數名 |
| `response_key` | 從 JSON 回傳中萃取的資料欄位 |

### C. 外部網頁搜尋 (Web Search)

當內部資料庫與 API 都查不到時，透過搜尋引擎取得網路資料。

```toml
[[databases]]
name = "db_web_search"
type = "web_search"
description = "網際網路搜尋引擎"

search_engine = "duckduckgo"       # 免費、免金鑰的搜尋引擎
max_results = 3                    # 最多參考幾篇網頁結果
```

| 參數 | 說明 |
|------|------|
| `search_engine` | 搜尋引擎供應商 |
| `max_results` | 每次搜尋回傳的最大結果數 |

---

## 8. Agent 定義 `[[agents]]`

定義多 Agent 架構中的每個 Agent。Router 根據意圖分類結果，透過 `Send()` fan-out 將請求派發給對應的 Agent 子圖。每個 Agent 是獨立的 LLM + Tools 迴圈。

```toml
[[agents]]
name = "product_expert"                          # Agent 唯一名稱
label = "產品規格專家"                             # 顯示用中文標籤
description = "負責回答產品規格、設定操作、保固相關問題"  # Agent 職責描述
tools = ["db_smartlock_manual", "transfer_to_human"]  # 可用工具列表
prompt_file = "agents/prompts/product_expert.md"      # System Prompt 檔案路徑
```

| 參數 | 說明 |
|------|------|
| `name` | Agent 唯一識別名，`[[intents]]` 的 `target` 會引用此名稱 |
| `label` | 中文顯示名稱，用於日誌與路徑追蹤 |
| `description` | Agent 職責描述 |
| `tools` | 工具清單，元素需對應 `[[databases]]` 的 `name` 或內建工具（如 `transfer_to_human`） |
| `prompt_file` | System Prompt 的 Markdown 檔案路徑（相對於專案根目錄） |

### 目前系統內建的 Agent

| Agent | 工具 | 用途 |
|-------|------|------|
| `product_expert` | `db_smartlock_manual` + `transfer_to_human` | 產品規格、設定操作、保固 |
| `troubleshooter` | `db_troubleshooting` + `transfer_to_human` | 故障排除、維修指引 |
| `order_clerk` | `db_order_api` + `transfer_to_human` | 訂單查詢、物流追蹤 |
| `web_researcher` | `db_web_search` + `transfer_to_human` | 網路搜尋補充資訊 |

> **擴充方式**：新增一個 `[[agents]]` 區塊 + 對應的 prompt 檔案 + `[[intents]]` 路由即可，無需修改程式碼。

---

## 9. 意圖偵測路由設定 `[[intents]]`

定義 Router 的「語意路由（Semantic Routing）」規則。Router 節點使用 LLM 根據這些定義進行意圖分類，支援**多意圖平行派發**（一個問題可同時命中多個意圖）。

```toml
[[intents]]
name = "order_status"                # 意圖唯一名稱
label = "查詢訂單或維修進度"            # 顯示用中文標籤
description = "使用者想查詢訂單進度、出貨狀況、物流狀態或維修進度"  # 給 LLM 的意圖描述
target = "order_clerk"               # 路由目標，對應 [[agents]] 的 name
require_slots = false                # 是否需要先完成槽位填充
```

| 參數 | 說明 |
|------|------|
| `name` | 意圖唯一識別名 |
| `label` | 中文顯示名稱 |
| `description` | 意圖描述，LLM 據此判斷使用者問題屬於哪個意圖。寫得越精確，分類越準確 |
| `target` | 路由目標，可填 `[[agents]]` 的 `name`、`"out_of_domain"` 或 `"human"` |
| `require_slots` | 是否要求先完成 `[required_slots]` 的槽位填充才進入 Agent |

### 目前系統內建的意圖

| 意圖 | 目標 Agent | 需要槽位 | 說明 |
|------|-----------|---------|------|
| `order_status` | `order_clerk` | 否 | 訂單/物流/維修進度查詢 |
| `troubleshooting` | `troubleshooter` | 是 | 設備故障排除 |
| `general_knowledge` | `product_expert` | 否 | 產品規格與操作問題（預設 Fallback） |
| `web_search` | `web_researcher` | 否 | 需要即時網路資訊的問題 |
| `out_of_domain` | `out_of_domain` | 否 | 非業務範圍，禮貌拒絕 |
| `transfer_human` | `human` | 否 | 使用者明確堅持轉接真人 |

---

## 10. 對話記憶儲存設定 `[memory]`

管理系統如何記住跨回合的歷史對話（LangGraph Checkpointer）以及語意摘要壓縮策略。透過 Memory Factory（`memory/__init__.py`）動態載入。

```toml
[memory]
type = "sqlite"                    # 可選: "memory" (暫存), "sqlite" (本地持久化), "postgres" (資料庫持久化)
sqlite_path = "./data/db/chat_history.db"  # sqlite 專用，資料庫檔案路徑
# postgres_uri_env = "POSTGRES_URI"        # PostgreSQL 連線字串（未來擴充）
max_messages_threshold = 10        # messages 超過此數量時觸發語意摘要壓縮
context_retention_pair = 2         # 壓縮後保留最近幾對 (human+ai) 訊息
```

| 參數 | 說明 |
|------|------|
| `type` | Checkpointer 類型。`"memory"` 僅存於記憶體（重啟即失）；`"sqlite"` 持久化至本地檔案；`"postgres"` 持久化至 PostgreSQL |
| `sqlite_path` | `sqlite` 類型專用，指定 `.db` 檔案路徑 |
| `max_messages_threshold` | `manage_memory` 節點的觸發門檻。當 `messages` 數量超過此值，LLM 會將舊訊息壓縮為結構化摘要 |
| `context_retention_pair` | 壓縮後保留的最近對話對數（1 對 = 1 human + 1 ai = 2 條 message） |

> **摘要壓縮流程**：`manage_memory` 節點呼叫 LLM（使用 `summarize_messages.md` 模板）將舊訊息壓縮為結構化摘要，透過 `RemoveMessage` API 刪除已壓縮的訊息，摘要存入 `state.summary`，由 `pre_process` 以 `[前情提要]` SystemMessage 注入後續流程。

---

## 11. 必填資訊收集 `[required_slots]`

定義特定意圖（`require_slots = true`）在進入 Agent 前，必須向使用者釐清的關鍵資訊（Slot Filling）。

```toml
[required_slots]
device_model = "使用者的電子鎖型號。"
device_brand = "使用者的電子鎖品牌。"
```

| 參數 | 說明 |
|------|------|
| Key（如 `device_model`） | 程式內部使用的槽位變數名 |
| Value（如 `"使用者的電子鎖型號。"`） | 給 LLM 看的欄位定義與提示，寫得越清楚，LLM 抽取的準確率越高 |

---

## 12. 使用者輪廓記憶設定 `[user_profile]`

管理動態使用者輪廓（User Profile），系統會在 `update_profile` 節點透過 LLM 從對話中萃取個人資訊（設備型號、地址、電話等），持久化至檔案系統。

```toml
[user_profile]
enabled = true                     # 是否啟用輪廓功能
profile_dir = "./data/profiles"    # 輪廓檔案儲存目錄

[user_profile.extraction]
phone_regex   = '09\d{2}[\-\s]?\d{3}[\-\s]?\d{3}'
address_regex = '[\u4e00-\u9fff]*(?:市|縣)[\u4e00-\u9fff]*(?:區|鄉|鎮|市)[\u4e00-\u9fff\d\s\-]*(?:路|街|巷|弄|號|樓)[\u4e00-\u9fff\d\s\-]*'
```

| 參數 | 說明 |
|------|------|
| `enabled` | 是否啟用使用者輪廓功能 |
| `profile_dir` | 輪廓 Markdown 檔案的儲存目錄，每位使用者一個 `{user_id}.md` 檔 |
| `phone_regex` | 電話號碼正則表達式（TOML 單引號 literal string，不轉義反斜線） |
| `address_regex` | 地址正則表達式（用於 `transfer_to_human` 個資提取） |

> **輪廓用途**：`pre_process` 載入輪廓注入對話；`update_profile` 在每輪結束後更新；`transfer_human` 從輪廓提取個資帶入轉接表單。
>
> **Extraction 子表**：`[user_profile.extraction]` 定義 `transfer_to_human` 節點與工具從對話中提取個資的 regex。支援國際化——修改 regex 即可適應不同國家的電話/地址格式，無需改動 Python 程式碼。`core/constants.py` 會從此處動態載入，若未設定則使用台灣格式作為 fallback。

---

## 13. 審計日誌儲存設定 `[storage]`

持久化原始對話紀錄（user_raw + user + ai），供事後審計與分析。透過 Storage Factory（`storage/__init__.py`）動態載入。

```toml
[storage]
type        = "sqlite"
sqlite_path = "./data/db/audit_log.db"
# postgres_uri_env = "POSTGRES_URI"
```

| 參數 | 說明 |
|------|------|
| `type` | 儲存類型。`"sqlite"` 持久化至本地檔案；`"postgres"` 持久化至 PostgreSQL（預留） |
| `sqlite_path` | `sqlite` 類型專用，指定 `.db` 檔案路徑 |
| `postgres_uri_env` | PostgreSQL 連線字串的環境變數名（未來擴充） |

> **角色區分**：`user_raw` 為 webhook 收到的原始碎裂訊息（debounce 之前）；`user` 為合併後送入 LangGraph 的訊息；`ai` 為 AI 回覆。

---

## 14. Prompt 檔案路徑對照表 `[prompts]`

集中管理所有 prompt 模板的路徑，避免路徑硬編碼在 Python 中。

```toml
[prompts]
router          = "agents/prompts/router.md"
summarizer      = "agents/prompts/summarize_messages.md"
merger          = "agents/prompts/merge_answers.md"
profile_updater = "agents/prompts/update_profile.md"
transfer_form   = "agents/prompts/transfer_human_form.md"
```

| 參數 | 說明 |
|------|------|
| `router` | Router 意圖分類 prompt 路徑 |
| `summarizer` | 語意摘要壓縮 prompt 路徑 |
| `merger` | 多 Agent 回覆合併 prompt 路徑 |
| `profile_updater` | 使用者輪廓萃取 prompt 路徑 |
| `transfer_form` | 轉接真人表單模板路徑 |

> Agent 各自的 prompt 路徑定義在 `[[agents]].prompt_file` 中，不在此表。

---

## 附錄：設定區塊與流程節點對應關係

| 設定區塊 | 對應流程節點 / 模組 |
|---------|-------------------|
| `[system]` | Router prompt、out_of_domain 判斷 |
| `[debounce]` | `app.py` 防抖層 |
| `[line_bot]` | `app.py` Loading 動畫 |
| `[templates]` | `app.py` 錯誤回覆範本 + Push API fallback |
| `[llm]` | 所有 LLM 呼叫（Router、Agent、manage_memory、merge_answers、update_profile） |
| `[embedding]` | `embeddings/__init__.py` → 全域 Embedding 引擎（ChromaDB 等向量檢索器自動套用） |
| `[[databases]]` | `tools/__init__.py` → Agent 工具 |
| `[[agents]]` | `graph/builder.py` → Agent 子圖動態建構 |
| `[[intents]]` | `graph/nodes.py` Router → `Send()` fan-out 派發 |
| `[memory]` | `memory/__init__.py` → Checkpointer + manage_memory 壓縮策略 |
| `[required_slots]` | `graph/nodes.py` Router 槽位檢查 |
| `[user_profile]` | `profiles/manager.py` → pre_process / update_profile |
| `[user_profile.extraction]` | `core/constants.py` → 電話/地址 regex 動態載入 |
| `[storage]` | `storage/__init__.py` → 審計日誌持久化 |
| `[prompts]` | `graph/nodes.py`、`tools/__init__.py` → prompt 路徑集中管理 |
