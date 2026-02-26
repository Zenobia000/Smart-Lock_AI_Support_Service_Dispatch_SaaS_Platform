# 綜合品質檢查清單 (Unified Quality Checklist) - 電子鎖智能客服與派工平台

---

**文件版本 (Document Version):** `v1.0`
**最後更新 (Last Updated):** `2026-02-25`
**主要作者 (Lead Author):** `技術負責人, 安全工程師`
**狀態 (Status):** `使用中 (In Use)`

---

## 目錄 (Table of Contents)

- [A. 核心安全原則 (Core Security Principles)](#a-核心安全原則-core-security-principles)
- [B. 數據生命週期安全與隱私 (Data Lifecycle Security & Privacy)](#b-數據生命週期安全與隱私-data-lifecycle-security--privacy)
- [C. 應用程式安全 (Application Security)](#c-應用程式安全-application-security)
- [D. 基礎設施與運維安全 (Infrastructure & Operations Security)](#d-基礎設施與運維安全-infrastructure--operations-security)
- [E. 合規性 (Compliance)](#e-合規性-compliance)
- [F. 審查結論與行動項 (Review Conclusion & Action Items)](#f-審查結論與行動項-review-conclusion--action-items)
- [G. 生產準備就緒 (Production Readiness)](#g-生產準備就緒-production-readiness)
  - [G.1 可觀測性 (Observability)](#g1-可觀測性-observability)
  - [G.2 可靠性與彈性 (Reliability & Resilience)](#g2-可靠性與彈性-reliability--resilience)
  - [G.3 性能與可擴展性 (Performance & Scalability)](#g3-性能與可擴展性-performance--scalability)
  - [G.4 可維護性與文檔 (Maintainability & Documentation)](#g4-可維護性與文檔-maintainability--documentation)

---

# 安全與隱私設計審查 (Security and Privacy Design Review) - 電子鎖智能客服與派工平台

## 目的

**目的**: 本檢查清單旨在為「電子鎖智能客服與派工 SaaS 平台 (SmartLock-SaaS)」提供一個統一的框架，用於在專案的關鍵階段（V1.0 AI 客服上線、V2.0 派工帳務上線）進行全面的安全、隱私和生產準備就緒評估。所有檢查項目均依據專案實際的技術棧（FastAPI + PostgreSQL + pgvector + Redis + Google Gemini 3 Pro + LINE Bot SDK）與業務需求（LINE Bot AI 客服、ProblemCard 診斷、三層解決引擎、技師派工、報價帳務）進行具體化填寫。

---

**審查對象 (Review Target):** `SmartLock-SaaS v1.0 (AI 智能客服系統) / v2.0 (技師派工與帳務平台)`

**審查日期 (Review Date):** `2026-02-25`

**審查人員 (Reviewers):** `技術架構師、安全工程師、核心開發團隊`

**相關文檔 (Related Documents):**
*   PRD 文檔: `docs/02_project_brief_and_prd.md`
*   架構設計文檔: `docs/05_architecture_and_design_document.md`
*   API 設計規範: `docs/06_api_design_specification.md`
*   資料庫 Schema: `SQL/Schema.sql`
*   ADR 文件: `docs/adrs/ADR-001 ~ ADR-008`

---

## A. 核心安全原則 (Core Security Principles)

*   `[x]` **最小權限 (Least Privilege):**
    - PostgreSQL 資料庫帳號依服務需求設定最小權限：FastAPI 應用帳號僅授予 `SELECT`, `INSERT`, `UPDATE`, `DELETE` 權限，禁止 `DROP`, `CREATE`, `ALTER`（Schema 變更由 Alembic migration 專用帳號執行）。
    - RBAC 三種角色（`admin`, `reviewer`, `technician`）各自僅能存取其職責範圍內的 API 端點：`technician` 僅能操作自身工單、`reviewer` 僅能存取對話記錄與 SOP 審核、`admin` 擁有全部管理權限。
    - LINE 消費者（`line_user`）僅透過 LINE Webhook 互動，無法直接呼叫 REST API。
    - Redis 連線僅限 Docker 內部網路存取，不暴露外部端口。
    - Google AI API Key 設定每日/每月用量上限 (usage cap)，防止 API Key 外洩時的無限制呼叫。

*   `[x]` **縱深防禦 (Defense in Depth):**
    - **第一層 (網路層):** Nginx 反向代理負責 SSL/TLS 終止、IP 級別的 Rate Limiting、DDoS 基礎防護。VPS 防火牆僅開放 80/443 端口。
    - **第二層 (應用層):** FastAPI middleware 負責 JWT Token 驗證、RBAC 權限檢查、Redis 級別的用戶 Rate Limiting、請求參數 Pydantic 驗證。
    - **第三層 (LINE 專屬):** LINE Webhook 端點每次請求均驗證 `X-Line-Signature` HMAC-SHA256 簽章，拒絕簽章不匹配的請求。
    - **第四層 (AI 安全):** LLM 輸入經 Prompt Injection 偵測層過濾、內容過濾層阻擋不當內容；LLM 輸出經 Output Guardrail 檢查，確保回覆限定於電子鎖服務範疇。
    - **第五層 (數據層):** PostgreSQL 僅在 Docker 內部網路暴露端口 5432，不對外開放。備份檔案加密儲存。

*   `[x]` **預設安全 (Secure by Default):**
    - FastAPI 應用預設啟用 CORS 白名單策略，僅允許 `CORS_ORIGINS` 環境變數中指定的來源。
    - 所有 HTTP 請求由 Nginx 一律回傳 `301` 導向 HTTPS。
    - JWT Token 預設有效期 1 小時（Access Token），Refresh Token 有效期 7 天。
    - Redis Session TTL 預設 1800 秒（30 分鐘），對話超時自動清理。
    - 資料庫連線使用 `postgresql+asyncpg://` (SSL mode) 加密連線。
    - Docker 容器預設以非 root 用戶運行。

*   `[x]` **攻擊面最小化 (Minimize Attack Surface):**
    - Docker Compose 部署架構中，僅 Nginx 容器暴露 80/443 端口至外部；PostgreSQL (5432)、Redis (6379)、FastAPI (8000/8001)、Next.js (3000) 均僅在 Docker 內部網路 `smartlock-net` 中可達。
    - FastAPI 自動生成的 OpenAPI 文檔端點 (`/docs`, `/redoc`) 在生產環境中關閉。
    - `/health` 端點不返回敏感資訊（僅回傳 `{"status": "ok"}`）。
    - `/metrics` 端點限定僅內部網路可存取（Nginx 配置攔截外部請求）。
    - 不啟用不必要的 PostgreSQL 擴展套件，僅啟用 `uuid-ossp` 和 `vector`。

*   `[x]` **職責分離 (Separation of Duties):**
    - SOP 自動生成（系統觸發）與 SOP 審核發布（`reviewer` / `admin` 角色）分離，AI 生成的 SOP 草稿必須經人工審核後方可納入知識庫。
    - 技師墊付款申報（`technician`）與墊付款核准（`admin`）分離。
    - 月度結算報表生成（系統自動）與結算核准（`admin`）分離。
    - 工單建立（系統自動匹配或管理員手動指派）與工單完工確認（`admin` 審核技師回報）分離。
    - 知識庫內容變更記錄完整的審計追蹤（操作者、時間、變更內容）。

## B. 數據生命週期安全與隱私 (Data Lifecycle Security & Privacy)

### B.1 數據分類與收集 (Data Classification & Collection)

*   `[x]` **數據分類 (Data Classification):**

    本系統處理的所有數據按敏感性分類如下：

    | 分類等級 | 數據類型 | 對應欄位/資源 |
    |:---|:---|:---|
    | **機密 (Confidential)** | API Keys, Channel Secrets, JWT Secrets, 資料庫密碼 | `.env` 中的 `GOOGLE_API_KEY`, `LINE_CHANNEL_SECRET`, `LINE_CHANNEL_ACCESS_TOKEN`, `JWT_SECRET`, `DATABASE_URL` |
    | **PII (個人識別資訊)** | LINE User ID, 手機號碼, Email, 地址, 消費者姓名, 技師姓名/電話/Email | `users.line_user_id`, `users.phone`, `users.email`, `users.address`, `users.display_name`, `technicians.name`, `technicians.phone`, `work_orders.customer_name`, `work_orders.customer_phone`, `work_orders.customer_address` |
    | **內部 (Internal)** | 對話記錄, ProblemCard, 工單內容, 帳務報表, 管理員帳號密碼 hash | `conversations`, `messages`, `problem_cards`, `work_orders`, `invoices`, `reconciliations`, `settlements` |
    | **公開 (Public)** | API 文件結構, 健康檢查端點, 電子鎖品牌/型號公開資訊 | `/health`, 公開 API schema |

*   `[x]` **數據最小化 (Data Minimization):**
    - 消費者初次互動時僅收集 `line_user_id` 和 `display_name`（由 LINE Get Profile API 取得），不主動索取其他個資。
    - 手機號碼 (`phone`)、Email (`email`)、地址 (`address`) 僅在 L3 轉人工或建立派工單時才收集，且明確告知消費者收集目的。
    - 系統不收集信用卡號、身分證字號等高風險數據（付款由線下處理，不整合第三方金流）。
    - 日誌中禁止記錄使用者完整訊息內容，僅記錄 `message_id` 和 `content_type`。

*   `[x]` **用戶同意/告知 (User Consent/Notification):**
    - 消費者首次加入 LINE 官方帳號時，Rich Menu 或歡迎訊息中包含隱私政策摘要與完整隱私政策連結。
    - 當 L3 流程需要收集手機號碼與地址時，AI 客服明確告知用途（「為了安排技師到府服務，我們需要您的聯絡電話和地址」）。
    - 管理員與技師帳號建立時，需勾選同意資料處理條款。

### B.2 數據傳輸 (Data in Transit)

*   `[x]` **傳輸加密 (Encryption in Transit):**
    - 所有外部通訊強制使用 HTTPS (TLS 1.2+)，Nginx 層設定 `ssl_protocols TLSv1.2 TLSv1.3`，禁用 TLS 1.0/1.1。
    - LINE Webhook 回調由 LINE Platform 以 HTTPS 發送至本系統。
    - FastAPI 向 Google Gemini 3 Pro API 的呼叫（Chat Completion, Embedding）全程 HTTPS。
    - FastAPI 向 LINE Messaging API 的回覆/推播呼叫全程 HTTPS。
    - HTTP 請求一律回傳 `301` 導向 HTTPS（Nginx 配置）。

*   `[x]` **內部傳輸加密 (Internal Encryption):**
    - Docker 內部網路中，FastAPI 至 PostgreSQL 的連線使用 `sslmode=require` 參數啟用 SSL 加密。
    - FastAPI 至 Redis 的連線在 Docker 內部網路中傳輸，Redis 配置 `requirepass` 密碼認證。
    - Next.js (V2.0) 至 FastAPI 的 API 呼叫經 Nginx 反向代理，走 Docker 內部網路。

*   `[x]` **證書管理 (Certificate Management):**
    - 生產環境使用 Let's Encrypt 免費 TLS 證書，透過 `certbot` 自動續期（到期前 30 天自動更新）。
    - Nginx 配置 `ssl_certificate` 與 `ssl_certificate_key` 路徑指向 Let's Encrypt 證書。
    - 設定監控告警：TLS 證書到期前 14 天觸發 P2 Warning 告警。
    - 加密套件配置遵循 Mozilla Modern Compatibility 建議。

### B.3 數據儲存 (Data at Rest)

*   `[x]` **儲存加密 (Encryption at Rest):**
    - PostgreSQL 數據檔案啟用作業系統層級的磁碟加密（LUKS / dm-crypt 或雲端提供的 EBS/Persistent Disk 加密）。
    - 敏感欄位加密策略：
      - `users.phone`, `users.email`, `users.address`：應用層 AES-256 加密後儲存，查詢時解密。
      - `work_orders.customer_phone`, `work_orders.customer_address`：同上。
      - `users.line_user_id`：作為主要查詢鍵，使用可搜尋的格式（不加密但做存取控制）。
    - 管理員與技師帳號密碼使用 Argon2id (或 bcrypt，cost factor >= 12) 加鹽雜湊儲存。

*   `[x]` **金鑰管理 (Key Management):**
    - V1.0 階段：所有密鑰儲存於 `.env` 檔案中，`.env` 列入 `.gitignore` 禁止提交版本控制。每個環境（dev/staging/prod）使用獨立的 `.env` 檔案，絕不共享密鑰。
    - 密鑰輪替策略：

      | 密鑰 | 輪替週期 | 輪替方式 |
      |:---|:---|:---|
      | `JWT_SECRET` | 每季度 | 更新 `.env` 後重啟服務 |
      | `GOOGLE_API_KEY` | 每季度 | Google Cloud Console 產生新 Key |
      | `LINE_CHANNEL_SECRET` | 按需 | LINE Developers Console 重新產生 |
      | `DATABASE_URL` (密碼) | 每季度 | PostgreSQL `ALTER ROLE` 更新密碼 |

    - V2.0+ 規劃：遷移至 HashiCorp Vault 或雲端 Secrets Manager 進行集中化密鑰管理。

*   `[x]` **數據備份安全:**
    - 每日 01:00 AM (UTC+8) 執行 `pg_dump` 全量備份，備份檔案使用 `gpg` 加密。
    - 備份檔案保留 30 天（PRD 需求），超過自動清理。
    - 備份儲存於獨立的備份目錄或 S3 bucket，與主資料庫隔離。
    - 備份存取權限限定僅 `admin` 角色帳號可下載/恢復。
    - 每月執行一次備份恢復驗證（還原至 staging 環境驗證數據完整性）。

### B.4 數據使用與處理 (Data Usage & Processing)

*   `[x]` **日誌記錄中的敏感資訊:**
    - 結構化日誌 (JSON 格式, `structlog`) 中禁止記錄以下敏感資訊：
      - 使用者完整訊息內容（`messages.content`）：僅記錄 `message_id` 和 `content_type`
      - 使用者手機號碼、地址、Email
      - JWT Token 完整內容（僅記錄 token 前 8 字元 + `...` 做識別）
      - API Keys / Channel Secrets
      - 管理員/技師密碼或密碼 hash
    - 允許記錄：`line_user_id`（LINE 平台公開 ID）、`conversation_id`、`request_id`、`resolution_level`、`similarity_score`、`latency_ms`、`token_usage`
    - LLM 呼叫日誌記錄：`prompt_tokens`, `completion_tokens`, `total_cost`, `latency_ms`, `model`, `resolution_level`（不記錄 prompt 完整內容）

*   `[x]` **第三方共享:**
    - **LINE Corporation**: 透過 LINE Messaging API 發送/接收訊息，LINE 平台保有其平台上的訊息副本（依 LINE 隱私政策）。
    - **Google (Gemini 3 Pro API)**: 使用者問題描述經 LLM 處理，Google API 依其資料處理條款處理。需確認 Google AI API 的資料保留政策，建議啟用「不將資料用於模型訓練」選項。
    - **Google (text-embedding-004)**: 文本經 Embedding API 向量化，同上。
    - 未與其他第三方共享用戶資料。
    - 隱私政策中明確告知消費者資料會經由 LINE 平台與 Google AI 服務處理。

### B.5 數據保留與銷毀 (Data Retention & Disposal)

*   `[x]` **保留策略 (Retention Policy):**

    | 數據類型 | 保留期限 | 依據 |
    |:---|:---|:---|
    | 對話記錄 (`conversations`, `messages`) | 1 年 | 營運分析與客訴回溯需求 |
    | ProblemCard (`problem_cards`) | 1 年 | 與對話記錄同步保留 |
    | 知識庫 (`case_entries`, `manual_chunks`) | 永久（除非手動下架） | 核心業務資產 |
    | SOP 草稿 (`sop_drafts`) | 永久（含已拒絕的草稿） | 審計追蹤 |
    | 工單 (`work_orders`) | 5 年 | 帳務與法律合規需求 |
    | 發票/結算 (`invoices`, `reconciliations`, `settlements`) | 7 年 | 台灣稅務法規要求 |
    | 使用者資料 (`users`) | 帳號停用後 1 年 | PDPA 合規 |
    | 系統日誌 (INFO+) | 30 天 | 營運監控 |
    | 系統日誌 (DEBUG) | 7 天 | 開發除錯 |
    | 資料庫備份 | 30 天 | PRD 需求 |

*   `[x]` **安全銷毀 (Secure Disposal):**
    - 過期的對話記錄與 ProblemCard 透過排程任務（每週執行）以 `DELETE` + `VACUUM` 方式清理。
    - 使用者要求刪除帳號時，執行以下流程：
      1. `users` 表中個人資訊欄位（`display_name`, `phone`, `email`, `address`, `picture_url`）設為 `NULL`
      2. `line_user_id` 保留但設 `is_active = FALSE`（防止重複建帳）
      3. 關聯的對話記錄中 `messages.content` 替換為 `[已刪除]`
    - 資料庫備份過期後由排程任務自動刪除（`find backup_dir -mtime +30 -delete`）。
    - VPS 退役時，執行磁碟全量覆寫清除。

## C. 應用程式安全 (Application Security)

### C.1 身份驗證 (Authentication)

*   `[x]` **密碼策略:**
    - 管理員與技師帳號密碼強制至少 12 字元，包含大小寫英文、數字、特殊符號各至少一個。
    - 密碼不得與帳號名稱相同，不得為常見弱密碼（維護弱密碼黑名單）。
    - V1.0 不提供 MFA（Multi-Factor Authentication），但架構預留 MFA 擴充介面。V2.0+ 規劃為 admin 角色啟用 TOTP MFA。
    - LINE 消費者不需密碼認證，以 LINE Platform 的 `source.userId` 作為身分識別。

*   `[x]` **憑證儲存:**
    - 管理員與技師帳號密碼使用 Argon2id 加鹽雜湊儲存（Python `argon2-cffi` 套件），參數：`time_cost=3`, `memory_cost=65536`, `parallelism=4`。
    - 禁止以明文、Base64、可逆加密方式儲存密碼。
    - 密碼重設使用一次性 Token（有效期 30 分鐘），不以 Email 發送明文密碼。

*   `[x]` **會話管理 (Session Management):**
    - **JWT Token 管理:**
      - Access Token 有效期：1 小時（`JWT_EXPIRY_HOURS` 環境變數設定）
      - Refresh Token 有效期：7 天
      - Token 載荷包含：`user_id`, `role` (`admin` / `reviewer` / `technician`), `exp`, `iat`
      - Token 簽名演算法：HS256（`JWT_SECRET` 環境變數）
      - 登出時將 Token 加入 Redis blacklist（TTL = Token 剩餘有效期）
    - **LINE 消費者 Session:**
      - Redis 儲存對話 Session（key: `session:{session_id}`），TTL = 1800 秒（30 分鐘無互動自動過期）
      - Session 包含多輪對話上下文 (`context` JSONB)、已收集的 ProblemCard 欄位
      - Session 過期後 Conversation 狀態轉為 `expired`
    - **安全 Headers:**
      - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
      - `X-Content-Type-Options: nosniff`
      - `X-Frame-Options: DENY`
      - `X-XSS-Protection: 1; mode=block`

*   `[x]` **暴力破解防護:**
    - 認證端點 (`POST /api/v1/auth/login`, `POST /api/v1/technicians/login`) Rate Limiting: 10 req/min per IP（Redis 計數器）。
    - 連續 5 次登入失敗後帳號鎖定 15 分鐘（Redis TTL 計數器）。
    - 鎖定期間返回 HTTP 429 並記錄安全事件日誌。
    - LINE Webhook 端點 Rate Limiting: 1000 req/min（Nginx 層級）。

### C.2 授權與訪問控制 (Authorization & Access Control)

*   `[x]` **物件級別授權 (Object-Level Authorization):**
    - 技師 (`technician` 角色) 僅能存取指派給自己的工單 (`work_orders WHERE technician_id = current_user.technician_id`)，不能查看其他技師的工單。
    - 技師僅能查看與自己相關的帳務資料 (`reconciliations`, `settlements` WHERE `technician_id = current_user.technician_id`)。
    - LINE 消費者僅能透過自己的 `line_user_id` 查詢自身的案件進度，不能查看他人資料。
    - API 端點在 Service 層實施物件級別權限檢查，不僅依賴 URL 路由保護。

*   `[x]` **功能級別授權 (Function-Level Authorization):**

    | API 端點 | admin | reviewer | technician | line_user |
    |:---|:---:|:---:|:---:|:---:|
    | `POST /api/v1/webhook/line` | - | - | - | LINE Signature |
    | `GET /api/v1/conversations` | O | O | X | X |
    | `POST /api/v1/knowledge-base/cases` | O | O | X | X |
    | `POST /api/v1/sop-drafts/{id}/approve` | O | O | X | X |
    | `GET /api/v2/work-orders` | O | X | O (自身) | X |
    | `PUT /api/v2/work-orders/{id}/accept` | X | X | O (自身) | X |
    | `GET /api/v2/invoices` | O | X | X | X |
    | `POST /api/v2/technicians` | O | X | X | X |
    | `GET /api/v2/reports/monthly` | O | X | X | X |

    - 所有 API 端點使用 FastAPI `Depends()` 注入 RBAC 權限檢查中間件。
    - 未認證請求一律返回 HTTP 401，權限不足返回 HTTP 403。

### C.3 輸入驗證與輸出編碼 (Input Validation & Output Encoding)

*   `[x]` **防止注入攻擊:**
    - **SQL Injection 防護:** 全系統使用 SQLAlchemy 2.0 ORM 參數化查詢，嚴禁原生 SQL 字串拼接。Code Review checklist 中加入 SQL 注入檢查項目。pgvector 向量搜尋查詢也使用 SQLAlchemy 參數化方式。
    - **命令注入防護:** 系統不執行外部系統命令，PDF 解析使用 PyMuPDF 純 Python 函式庫。
    - **Prompt Injection 防護 (AI 專屬):**
      1. System Prompt 與 User Input 嚴格分離，使用 LangChain 的 `SystemMessage` / `HumanMessage` 明確區隔。
      2. 使用者輸入在送入 LLM 前經 sanitization 處理，過濾以下注入模式：
         - 「忽略先前指令」「列出你的 system prompt」「扮演另一個角色」等中英文注入模式
         - 維護一份注入模式黑名單（支援正則表達式），可動態更新
      3. LLM 輸出經後處理過濾，檢測是否包含 System Prompt 片段（正則匹配）。
      4. 所有被攔截的注入嘗試記錄至安全日誌（含 `line_user_id`, `conversation_id`, `intercepted_pattern`）。
      5. 目標：Prompt Injection 攔截率 >= 95%，正常對話誤攔率 < 1%。

*   `[x]` **防止跨站腳本 (XSS):**
    - V1.0 Admin Panel (Jinja2 + HTMX)：Jinja2 模板引擎預設啟用 HTML 自動轉義 (`autoescape=True`)。
    - V2.0 前端 (Next.js + React)：React JSX 預設對所有插值內容進行 HTML 轉義。禁止使用 `dangerouslySetInnerHTML`，除非內容已經過 DOMPurify 消毒。
    - API 回應設定 `Content-Type: application/json`，Nginx 設定 `X-Content-Type-Options: nosniff`。
    - Content Security Policy (CSP) 配置：
      ```
      Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' https:; connect-src 'self' https://api.smartlock-saas.com;
      ```

*   `[x]` **防止跨站請求偽造 (CSRF):**
    - Admin Panel 與 Technician Web App 使用 JWT Bearer Token 認證（不使用 Cookie 傳遞），天然防禦 CSRF。
    - 若 V2.0 Next.js 引入 Cookie-based session，須同時啟用 `SameSite=Strict` 屬性。
    - LINE Webhook 使用 `X-Line-Signature` HMAC-SHA256 簽章驗證，具備等效的請求偽造防護。

### C.4 API 安全 (API Security)

*   `[x]` **API 認證/授權:**
    - **LINE Webhook (`POST /api/v1/webhook/line`):** 使用 LINE Platform 的 `X-Line-Signature` HMAC-SHA256 簽章驗證。Channel Secret 用於計算簽章比對值。
    - **Admin Panel API:** JWT Bearer Token 認證（`Authorization: Bearer <access_token>`），Token 中包含 `role` claim。
    - **Technician App API (V2.0):** 獨立的 JWT Bearer Token 認證，Token 中包含 `technician_id` 和 `role: "technician"` claim。
    - **公開端點:** 僅 `/health`, `/api/v1/auth/login`, `/api/v1/technicians/login` 不需認證。

*   `[x]` **速率限制:**

    | 端點類型 | 限制 | 實現層級 | 超過限制回應 |
    |:---|:---|:---|:---|
    | LINE Webhook | 1000 req/min | Nginx `limit_req_zone` | HTTP 429 |
    | Auth 端點 | 10 req/min per IP | Redis 滑動窗口計數器 | HTTP 429 + `RateLimit-*` Headers |
    | 一般 API | 200 req/min per token | Redis 滑動窗口計數器 | HTTP 429 + `RateLimit-*` Headers |
    | Vector Search | 30 req/min per token | Redis 滑動窗口計數器 | HTTP 429 |

    - 所有 API 回應包含 Rate Limiting Headers：`RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset`。

*   `[x]` **參數校驗:**
    - 所有 API 輸入使用 Pydantic v2 schema 進行嚴格的白名單驗證：
      - `brand`: `str`, 最大長度 100，enum 白名單（Yale, Samsung, Gateman, Philips 等已知品牌）
      - `model`: `str`, 最大長度 100，正則驗證格式
      - `status`: 嚴格 enum 驗證（`incomplete`, `confirmed`, `resolved`, `escalated`）
      - `urgency`: 嚴格 enum 驗證（`low`, `normal`, `high`, `urgent`）
      - UUID 欄位使用 Pydantic `UUID4` 型別驗證
      - 日期時間欄位使用 ISO 8601 格式驗證
    - LINE 消費者訊息輸入長度限制：單條文字訊息 < 2000 字元。
    - 檔案上傳驗證：
      - PDF 手冊：僅接受 `.pdf`，大小限制 50MB
      - 完工報告照片：僅接受 `.jpg`, `.jpeg`, `.png`，單張 < 5MB
      - MIME Type 驗證（不僅檢查副檔名）

*   `[x]` **避免數據過度暴露:**
    - API 回應使用 Pydantic Response Schema 明確定義回傳欄位，不直接回傳 SQLAlchemy ORM 物件。
    - `users` 資料回傳時排除 `password_hash` 欄位。
    - `technicians` 列表 API 不回傳技師的個人電話與 Email（僅管理員詳情頁可見）。
    - 對話記錄 API 不回傳 `messages.metadata` 中的 `token_usage` 和 `latency_ms`（僅管理員統計 API 可見）。
    - 錯誤回應不暴露內部實作細節（不返回 stack trace、SQL 語句、檔案路徑）。

### C.5 依賴庫安全 (Dependency Security)

*   `[x]` **漏洞掃描:**
    - CI/CD Pipeline（GitHub Actions）中整合 `pip-audit` 每次 PR 自動掃描 Python 依賴庫已知漏洞。
    - V2.0 前端 Next.js 專案整合 `npm audit` 自動掃描 Node.js 依賴庫。
    - 啟用 GitHub Dependabot，自動偵測依賴庫安全更新並建立 PR。
    - 每週人工審查一次 Dependabot 告警。

*   `[x]` **更新策略:**
    - **關鍵依賴庫 (Critical):** `fastapi`, `sqlalchemy`, `langchain`, `line-bot-sdk-python`, `pydantic`, `uvicorn` -- 收到 CVE 通報後 72 小時內更新。
    - **一般依賴庫:** 每月定期更新一次，透過 CI/CD 自動化測試驗證相容性。
    - `pyproject.toml` 中使用版本區間鎖定（如 `fastapi = ">=0.110,<1.0"`），`poetry.lock` 鎖定確切版本。
    - 禁止引入無維護者、最後更新超過 2 年的依賴庫。

## D. 基礎設施與運維安全 (Infrastructure & Operations Security)

### D.1 網路安全 (Network Security)

*   `[x]` **防火牆/安全組:**
    - VPS 主機防火牆（`ufw` 或雲端安全組）規則：

      | 方向 | 端口 | 來源 | 說明 |
      |:---|:---|:---|:---|
      | Inbound | 80/tcp | 0.0.0.0/0 | HTTP -> 301 HTTPS 導向 |
      | Inbound | 443/tcp | 0.0.0.0/0 | HTTPS (Nginx) |
      | Inbound | 22/tcp | 管理員 IP 白名單 | SSH 管理存取 |
      | Outbound | 443/tcp | 0.0.0.0/0 | Google AI API, LINE API |
      | Outbound | 53/tcp+udp | 0.0.0.0/0 | DNS |
      | 其他 | 全部 | - | DENY (預設拒絕) |

    - Docker 內部網路 (`smartlock-net`) 中的服務端口（5432, 6379, 8000, 3000）不暴露至主機外部。
    - SSH 存取：禁用密碼登入，僅允許 SSH Key 認證；更改預設 SSH 端口（非 22）。

*   `[x]` **DDoS 防護:**
    - Nginx 層級：
      - `limit_req_zone` 設定全域 IP 級別請求限制（1000 req/min per IP）
      - `limit_conn_zone` 設定同一 IP 最大並發連線數（50）
      - `client_max_body_size 50M` 限制請求體大小
      - `client_body_timeout 10s` 限制請求體接收超時
    - 若部署於雲端，啟用雲端提供的 DDoS 防護服務（如 AWS Shield Standard, GCP Cloud Armor）。
    - V2.0+ 規劃：評估部署 Cloudflare 或類似 CDN/WAF 前端防護。

### D.2 機密管理 (Secrets Management)

*   `[x]` **安全儲存:**
    - 所有機密資訊（API Keys, Channel Secrets, JWT Secrets, 資料庫密碼）儲存於 `.env` 檔案中，透過 Docker Compose `env_file` 指令注入容器環境變數。
    - `.env` 檔案列入 `.gitignore`，嚴禁提交至版本控制。
    - 提供 `.env.example` 範本檔案（僅含 key 名稱，value 為空或範例值）供新開發者參考。
    - 程式碼中嚴禁硬編碼任何密鑰（CI/CD Pipeline 加入 `detect-secrets` 或 `gitleaks` 掃描）。
    - 環境變數清單：

      | 變數名稱 | 敏感等級 | 說明 |
      |:---|:---|:---|
      | `DATABASE_URL` | 高 | PostgreSQL 連線字串（含帳密） |
      | `REDIS_URL` | 中 | Redis 連線字串 |
      | `GOOGLE_API_KEY` | 高 | Google Gemini 3 Pro API 金鑰 |
      | `LINE_CHANNEL_SECRET` | 高 | LINE Webhook 簽章驗證密鑰 |
      | `LINE_CHANNEL_ACCESS_TOKEN` | 高 | LINE Messaging API 存取權杖 |
      | `JWT_SECRET` | 高 | JWT Token 簽名密鑰 |

*   `[x]` **權限與輪換:**
    - `.env` 檔案的 Linux 檔案權限設定為 `600`（僅擁有者可讀寫）。
    - 密鑰輪替策略：每季度輪替 `JWT_SECRET`, `GOOGLE_API_KEY`, 資料庫密碼。LINE 相關密鑰按需輪替。
    - 密鑰輪替時須同步更新所有使用該密鑰的環境（staging/production），並驗證服務正常運作。
    - 密鑰洩露應急流程：立即撤銷洩露的密鑰 -> 產生新密鑰 -> 更新所有環境 -> 檢查審計日誌是否有異常存取。

### D.3 Docker/容器安全 (Container Security)

*   `[x]` **最小化基礎鏡像:**
    - FastAPI 應用使用 `python:3.11-slim` 作為基礎鏡像（非 full image），減少攻擊面。
    - PostgreSQL 使用 `postgres:16-alpine`。
    - Redis 使用 `redis:7-alpine`。
    - Nginx 使用 `nginx:alpine`。
    - Next.js (V2.0) 使用 multi-stage build：`node:20-alpine` 建置 -> `node:20-alpine` 運行。
    - 禁止使用 `latest` tag，明確鎖定版本號。

*   `[x]` **非 Root 用戶運行:**
    - FastAPI Dockerfile 中建立專用用戶並切換：
      ```dockerfile
      RUN adduser --disabled-password --gecos '' appuser
      USER appuser
      ```
    - PostgreSQL 容器預設以 `postgres` 用戶運行（非 root）。
    - Redis 容器以 `redis` 用戶運行。
    - Nginx 容器的 worker process 以 `nginx` 用戶運行。
    - Docker Compose 中不使用 `--privileged` 旗標。

*   `[x]` **鏡像掃描:**
    - CI/CD Pipeline 中加入 Docker 鏡像漏洞掃描（使用 `trivy` 或 `docker scout`）。
    - 阻擋含有 Critical / High 等級漏洞的鏡像推送至 Container Registry。
    - 定期（每週）重新建置並掃描鏡像，即使程式碼未變更（基礎鏡像可能有新漏洞）。

### D.4 日誌與監控 (Logging & Monitoring)

*   `[x]` **安全事件日誌:**
    記錄以下安全相關事件至結構化日誌：

    | 事件類型 | 日誌等級 | 記錄內容 |
    |:---|:---|:---|
    | 登入成功 | INFO | `user_id`, `role`, `ip_address`, `timestamp` |
    | 登入失敗 | WARN | `username`, `ip_address`, `failure_reason`, `attempt_count` |
    | 帳號鎖定 | WARN | `username`, `ip_address`, `lock_duration` |
    | JWT Token 被加入黑名單 | INFO | `user_id`, `token_prefix`, `reason` |
    | RBAC 權限拒絕 | WARN | `user_id`, `role`, `requested_resource`, `requested_action` |
    | LINE Webhook 簽章驗證失敗 | ERROR | `ip_address`, `request_headers` (脫敏), `timestamp` |
    | Prompt Injection 偵測 | WARN | `line_user_id`, `conversation_id`, `intercepted_pattern`, `user_input_hash` |
    | 不當內容攔截 | WARN | `line_user_id`, `conversation_id`, `content_category` |
    | API Rate Limit 觸發 | WARN | `ip_address` / `token_prefix`, `endpoint`, `limit_type` |
    | 管理員操作（刪除/修改知識庫） | INFO | `admin_id`, `action`, `target_resource`, `target_id` |
    | 密鑰存取嘗試 | ERROR | `ip_address`, `requested_secret`, `timestamp` |

*   `[x]` **安全告警:**
    - 設定以下即時告警（透過 LINE 群組通知 + Email）：

      | 告警條件 | 嚴重度 | 通知對象 |
      |:---|:---|:---|
      | 同一 IP 連續登入失敗 > 10 次 / 5 分鐘 | P1 - Critical | 安全工程師 + Tech Lead |
      | LINE Webhook 簽章驗證失敗率 > 5% / 分鐘 | P1 - Critical | 安全工程師 + Tech Lead |
      | Prompt Injection 偵測次數 > 20 次 / 小時 | P2 - Warning | Tech Lead |
      | 非上班時間的 admin 登入 | P3 - Info | Tech Lead |
      | API 5xx 錯誤率 > 5% 持續 3 分鐘 | P1 - Critical | On-call 負責人 |
      | 資料庫連線池使用率 > 90% | P2 - Warning | On-call 負責人 |
      | LLM API 連續失敗 > 3 次 | P1 - Critical | On-call 負責人 |

## E. 合規性 (Compliance)

*   `[x]` **法規識別:**
    本專案需遵循的法律法規：

    | 法規 | 適用範圍 | 關鍵要求 |
    |:---|:---|:---|
    | **台灣個人資料保護法 (PDPA)** | 消費者 PII（LINE User ID, 手機, 地址, Email）、技師個資 | 告知義務、目的外利用限制、資料安全維護、當事人行使權利（查詢/更正/刪除） |
    | **消費者保護法** | 消費者權益相關 | 服務條款明確揭露、定型化契約審閱期 |
    | **電子簽章法** | 電子發票、電子憑證 | V2.0 帳務模組產生的電子憑證需符合法定格式 |
    | **稅捐稽徵法** | 帳務記錄保留 | 帳務資料保留至少 7 年 |
    | **LINE Platform 使用條款** | LINE Messaging API 使用 | 遵守 LINE 平台政策，不得發送垃圾訊息，正確使用 Push/Reply Message |

*   `[x]` **合規性措施:**
    - **PDPA 合規：**
      - 隱私政策：LINE 官方帳號 Rich Menu 中提供隱私政策連結，明確揭露資料收集範圍、用途、保存期限、第三方共享對象（LINE, Google AI）。
      - 資料存取權：消費者可透過 LINE 對話要求查詢/更正/刪除個人資料（由管理員在 Admin Panel 處理）。
      - 資料安全義務：AES-256 加密靜態 PII、TLS 1.2+ 傳輸加密、RBAC 存取控制、定期安全審計。
      - 資料外洩通報：發現資料外洩後 72 小時內通報主管機關。
    - **LINE 平台合規：**
      - Push Message 僅在消費者主動互動後發送（不發送未經同意的行銷訊息）。
      - Webhook 端點正確驗證 LINE 簽章。
      - 遵守 LINE Messaging API 使用量限制。
    - **帳務合規 (V2.0)：**
      - 記帳憑證格式符合台灣會計準則（借方/貸方科目、金額、摘要）。
      - 發票與結算記錄保留 7 年。
      - 憑證編號自動遞增，不重複。

## F. 審查結論與行動項 (Review Conclusion & Action Items)

*   **主要風險 (Key Risks Identified):**
    *   `風險 1: Prompt Injection 攻擊可能繞過現有防護，導致 AI 產生不當回應或洩露 System Prompt。評級: 高`
    *   `風險 2: Google Gemini 3 Pro API Key 洩露可能導致 API 被濫用，產生高額費用。評級: 高`
    *   `風險 3: LINE Webhook 未正確驗證簽章可能導致偽造請求注入惡意數據。評級: 高`
    *   `風險 4: V1.0 階段密鑰管理使用 .env 檔案，缺乏集中化管理與自動輪替。評級: 中`
    *   `風險 5: PII 資料（手機、地址）若未在應用層加密，資料庫遭入侵時直接暴露。評級: 中`
    *   `風險 6: LLM 幻覺 (Hallucination) 可能產生錯誤的電子鎖維修建議，造成安全風險。評級: 中`
    *   `風險 7: 缺乏 MFA 機制，admin 帳號若密碼洩露則完全失守。評級: 中`

*   **行動項 (Action Items):**

| # | 行動項描述 | 負責人 | 預計完成日期 | 狀態 |
|:-:| :--- | :--- | :--- | :--- |
| 1 | 實作 Prompt Injection 偵測層（正則 + ML 分類器），建立注入模式黑名單，並撰寫紅隊測試案例 | 安全工程師 | V1.0 Phase 2 (W10) | `待辦` |
| 2 | 實作 Output Guardrail，確保 AI 回覆限定於電子鎖服務範疇，不包含危險操作建議 | AI 工程師 | V1.0 Phase 2 (W10) | `待辦` |
| 3 | 在應用層實作 PII 欄位 AES-256 加密（`users.phone`, `users.email`, `users.address`, `work_orders.customer_*`） | 後端工程師 | V1.0 Phase 1 (W5) | `待辦` |
| 4 | 配置 Google AI API 每日/每月用量上限告警，設定費用預算閾值 | Tech Lead | V1.0 Phase 1 (W3) | `待辦` |
| 5 | 撰寫 LINE Webhook 簽章驗證的整合測試，覆蓋正確簽章、錯誤簽章、空簽章三種情境 | QA 工程師 | V1.0 Phase 1 (W4) | `待辦` |
| 6 | CI/CD Pipeline 整合 `pip-audit`, `trivy`, `gitleaks` 安全掃描工具 | DevOps 工程師 | V1.0 Phase 1 (W4) | `待辦` |
| 7 | 撰寫隱私政策文件（繁體中文），並設定 LINE Rich Menu 隱私政策連結 | PM + 法務 | V1.0 Phase 3 (W13) | `待辦` |
| 8 | V2.0 啟動前評估並導入 HashiCorp Vault 或雲端 Secrets Manager 取代 .env 檔案 | 安全工程師 | V2.0 Phase 5 (W18) | `待辦` |
| 9 | V2.0 啟動前為 admin 角色實作 TOTP MFA 機制 | 後端工程師 | V2.0 Phase 5 (W19) | `待辦` |
| 10 | 建立安全事件應急回應流程 (Incident Response Plan)，包含資料外洩通報 SOP | 安全工程師 + PM | V1.0 Phase 3 (W14) | `待辦` |

*   **整體評估 (Overall Assessment):**
    本專案在架構設計階段已充分考慮安全性（Clean Architecture 分層、RBAC、LINE 簽章驗證、Prompt Injection 防護規劃），但在以下方面需在上線前完成強化：(1) Prompt Injection 偵測與 Output Guardrail 的實作與紅隊測試；(2) PII 欄位應用層加密的實作；(3) CI/CD 安全掃描工具鏈的整合。建議在完成上述 P0 行動項（#1 ~ #6）後方可進行 V1.0 UAT 驗收。V2.0 上線前須額外完成行動項 #8 (密鑰集中管理) 和 #9 (MFA)。

---

**簽署 (Sign-off):**

*   **安全審查團隊代表:** _______________
*   **專案/功能負責人:** _______________

---

## G. 生產準備就緒 (Production Readiness)

*此部分旨在確保「電子鎖智能客服與派工平台」在 V1.0 / V2.0 上線前，在可觀測性、可靠性、可擴展性和可維護性等方面已達到生產標準。*

### G.1 可觀測性 (Observability)

*   `[x]` **監控儀表板 (Monitoring Dashboard):**
    - 建立系統監控儀表板（Grafana 或自建 Admin Panel 儀表板），包含以下面板：
      - **系統健康:** CPU/Memory 使用率、磁碟使用率、Docker 容器狀態
      - **API 效能:** 請求量趨勢、P50/P95/P99 延遲、HTTP 狀態碼分佈
      - **AI 引擎:** LLM 呼叫延遲、Token 使用量、累計費用、各層解決比例 (L1/L2/L3)
      - **業務指標:** 今日對話數、自助解決率、ProblemCard 數量、知識庫案例數
      - **V2.0 派工:** 今日工單數、平均派工至完工時間、技師在線數、異常工單數

*   `[x]` **核心指標 (Key Metrics - SLIs):**
    - 已定義並透過 FastAPI middleware 暴露以下 SLIs：

      | SLI | 指標名稱 | 類型 | SLO 目標 |
      |:---|:---|:---|:---|
      | 請求延遲 | `api_request_duration_seconds` | Histogram | P95 < 2s (一般 API), P95 < 10s (LLM 相關) |
      | 錯誤率 | `api_request_total{status=~"5.."}` / `api_request_total` | Counter | < 1% |
      | 可用性 | Uptime | Gauge | >= 99.5% |
      | L1 搜尋延遲 | `vector_search_duration_seconds` | Histogram | P95 < 3s |
      | LLM 呼叫延遲 | `llm_call_duration_seconds` | Histogram | P95 < 10s |
      | AI 首次回應時間 | `ai_first_response_seconds` | Histogram | P95 < 5s |

    - 透過 `/metrics` 端點（Prometheus 格式）暴露指標。

*   `[x]` **日誌 (Logging):**
    - 使用 Python `structlog` 產出 JSON 結構化日誌，必含欄位：`timestamp`, `level`, `message`, `request_id`, `module`
    - 日誌等級：
      - Development: `DEBUG`
      - Staging: `INFO`
      - Production: `INFO`（可透過 `LOG_LEVEL` 環境變數在運行時調整為 `DEBUG`，無需重啟）
    - V1.0: 日誌輸出至 Docker stdout/stderr，由 Docker logging driver 管理（json-file + log rotation，每檔 100MB，保留 5 個）
    - V2.0+: 可接入 Loki / ELK Stack 中央日誌系統
    - 日誌保留：INFO+ 保留 30 天，DEBUG 保留 7 天

*   `[x]` **全鏈路追蹤 (Distributed Tracing):**
    - 每個 API 請求由 FastAPI middleware 自動產生唯一 `request_id`（UUID v4），並透過 `X-Request-ID` Header 回傳。
    - `request_id` 貫穿整條處理鏈路：Webhook Handler -> Conversation Manager -> ProblemCard Engine -> Three-Layer Resolver -> LLM Gateway -> LINE SDK Adapter，記錄於每條日誌中。
    - V1.0 使用自建的 `request_id` 追蹤。V2.0+ 規劃接入 OpenTelemetry，支援 trace / span 級別追蹤。
    - LLM 呼叫日誌額外記錄：`prompt_tokens`, `completion_tokens`, `total_cost`, `latency_ms`, `model`, `resolution_level`。

*   `[x]` **告警 (Alerting):**
    - 已配置以下關鍵故障場景的自動告警：

      | 告警名稱 | 觸發條件 | 嚴重度 | 通知管道 |
      |:---|:---|:---|:---|
      | API 高延遲 | P95 > 5s 持續 5 分鐘 | P2 - Warning | LINE 群組通知 |
      | API 錯誤率飆升 | 5xx 比率 > 5% 持續 3 分鐘 | P1 - Critical | LINE 群組 + 電話 |
      | LLM 呼叫失敗 | 連續失敗 > 3 次 | P1 - Critical | LINE 群組通知 |
      | LLM 費用超標 | 當日費用 > 預算 80% | P2 - Warning | LINE 群組 + Email |
      | 資料庫連線耗盡 | 連線池 > 90% | P2 - Warning | LINE 群組通知 |
      | 磁碟使用率 | > 85% | P2 - Warning | LINE 群組通知 |
      | 備份失敗 | 每日備份未在 02:00 AM 前完成 | P1 - Critical | LINE 群組 + Email |
      | Redis 不可達 | 健康檢查失敗 | P1 - Critical | LINE 群組 + 電話 |
      | TLS 證書即將過期 | 到期前 14 天 | P2 - Warning | Email |

    - 告警通知至 On-call 負責人的 LINE 群組 + Email，P1 級別同時電話通知。

### G.2 可靠性與彈性 (Reliability & Resilience)

*   `[x]` **健康檢查 (Health Checks):**
    - 已實現 `GET /health` 端點，回傳系統健康狀態：
      ```json
      {
        "status": "ok",
        "version": "1.0.0",
        "uptime_seconds": 86400,
        "checks": {
          "database": "ok",
          "redis": "ok",
          "google_ai": "ok"
        }
      }
      ```
    - 健康檢查包含：PostgreSQL 連線可達、Redis 連線可達、Google AI API 可達（輕量 ping）。
    - Docker Compose 中配置 `healthcheck` 指令，每 30 秒檢查一次。
    - Nginx 上游健康檢查：自動摘除回應異常的 FastAPI Worker。

*   `[x]` **優雅啟停 (Graceful Shutdown):**
    - FastAPI / Uvicorn 已正確處理 `SIGTERM` 信號：
      1. 停止接收新請求
      2. 等待進行中的請求完成（最長 30 秒）
      3. 關閉 PostgreSQL 連線池 (`dispose()`)
      4. 關閉 Redis 連線
      5. 退出進程
    - Docker Compose `stop_grace_period: 30s`，給予容器 30 秒優雅關閉時間。
    - 部署時使用 Rolling Restart（先啟動新容器確認健康後再停止舊容器），確保零停機部署。

*   `[x]` **重試與超時 (Retries & Timeouts):**

    | 外部服務 | 超時設定 | 重試策略 | 降級策略 |
    |:---|:---|:---|:---|
    | Google Gemini 3 Pro API | 30 秒 | 3 次，指數退避 (1s, 2s, 4s) | 回退至 L1 知識庫搜尋 + L3 轉人工 |
    | Google Embedding API | 10 秒 | 3 次，指數退避 | 排入重試佇列，稍後補算 |
    | LINE Messaging API (Reply) | 10 秒 | 2 次 | 記錄失敗日誌，不阻塞主流程 |
    | LINE Messaging API (Push) | 10 秒 | 3 次，指數退避 | 記錄失敗日誌，排入重試佇列 |
    | PostgreSQL 查詢 | 5 秒 | 不重試 | 返回 HTTP 500 |
    | Redis 操作 | 2 秒 | 1 次 | Session 丟失時從 DB 重建 |

    - LINE Webhook 必須在 1 秒內回傳 HTTP 200，所有 LLM 呼叫（2-10 秒）透過 `asyncio.create_task()` 非同步處理，以 Push Message 回覆。

*   `[x]` **故障轉移 (Failover):**
    - **FastAPI Workers:** Docker Compose 支援 `--scale api=2` 配置多 Worker，Nginx 負載均衡（round-robin），單 Worker 故障時流量自動切換至健康 Worker。
    - **PostgreSQL:** V1.0 單節點，依賴每日備份恢復。V2.0+ 規劃 PostgreSQL Streaming Replication（1 主 + 1 從），從庫自動 promote 為主庫。
    - **Redis:** V1.0 單節點，Session 丟失時從 DB 重建對話上下文。V2.0+ 規劃 Redis Sentinel 高可用方案。
    - **LLM 降級:** Google AI API 不可用時，L2 RAG 功能降級，系統回退至 L1 知識庫搜尋 + L3 轉人工。LangChain 抽象層允許快速切換至備用 LLM Provider（如 OpenAI）。

*   `[x]` **備份與恢復 (Backup & Recovery):**
    - **自動備份:**
      - 每日 01:00 AM (UTC+8) 由 `backup` 容器執行 `pg_dump --format=custom` 全量備份
      - 備份檔案命名格式：`smartlock_backup_YYYYMMDD_HHMMSS.dump.gpg`
      - 備份檔案加密後儲存至 `backup_data` Volume（或 S3 bucket）
      - 保留 30 天（PRD 需求），超過自動清理
    - **恢復流程:**
      1. 識別需恢復的備份檔案
      2. 解密備份檔案：`gpg --decrypt backup_file.dump.gpg > backup_file.dump`
      3. 停止 FastAPI 服務
      4. 恢復資料庫：`pg_restore --clean --dbname=smartlock backup_file.dump`
      5. 驗證數據完整性
      6. 重啟 FastAPI 服務
      7. 執行 smoke test 驗證
    - **恢復演練:** 每月在 Staging 環境執行一次恢復演練，記錄 RTO (Recovery Time Objective)。
    - **目標 RTO/RPO:**
      - RPO (Recovery Point Objective): 24 小時（每日備份間隔）
      - RTO (Recovery Time Objective): 1 小時

### G.3 性能與可擴展性 (Performance & Scalability)

*   `[x]` **負載測試 (Load Testing):**
    - V1.0 上線前使用 `k6` 或 `Locust` 執行以下負載測試場景：

      | 場景 | 目標並發 | 持續時間 | 關注指標 |
      |:---|:---|:---|:---|
      | LINE Webhook 模擬 | 50 concurrent users | 10 分鐘 | P95 延遲 < 1s（Webhook 回應）, 錯誤率 < 0.1% |
      | 知識庫向量搜尋 | 30 req/s | 5 分鐘 | P95 延遲 < 3s, PG 連線池使用率 < 80% |
      | Admin Panel API | 20 concurrent users | 10 分鐘 | P95 延遲 < 2s |
      | RAG Pipeline (L2) | 10 concurrent users | 5 分鐘 | P95 延遲 < 10s |
      | 混合場景 (模擬生產) | 50 concurrent users | 30 分鐘 | 系統穩定不崩潰, 無 OOM |

    - V2.0 增加：技師工作台 API (50 concurrent), 派工匹配 (20 req/s), 帳務查詢 (10 concurrent)

*   `[x]` **容量規劃 (Capacity Planning):**
    - V1.0 資源規劃（基於 50 並發用戶）：

      | 資源 | 最低配置 | 建議配置 | 說明 |
      |:---|:---|:---|:---|
      | VPS CPU | 2 vCPU | 4 vCPU | FastAPI async I/O 密集 |
      | VPS Memory | 4 GB | 8 GB | PostgreSQL + Redis + FastAPI Workers |
      | 磁碟 | 50 GB SSD | 100 GB SSD | 資料庫 + 備份 + 日誌 + PDF 手冊 |
      | PostgreSQL 連線池 | 10 | 20 | asyncpg pool_size |
      | Redis Memory | 256 MB | 512 MB | Session Cache + Rate Limiting |

    - V2.0 建議升級至 8 vCPU / 16 GB RAM，支援 100 並發用戶。
    - pgvector 向量索引記憶體預估：20K 筆 768 維向量約 120 MB。

*   `[x]` **水平擴展 (Horizontal Scaling):**
    - FastAPI 應用設計為無狀態（Session 存 Redis、數據存 PostgreSQL），可透過 `docker-compose --scale api=N` 水平擴展 Worker 數量。
    - Nginx 自動負載均衡至多個 FastAPI Worker。
    - V2.0 Next.js 前端同樣無狀態，可水平擴展。
    - 對話狀態存儲於 Redis（非 Worker 本地記憶體），任何 Worker 均可處理同一用戶的後續請求。

*   `[x]` **依賴擴展性:**
    - **PostgreSQL:** V1.0 單節點足以應付預估負載（500-2000 筆 CaseEntry, 5K-20K ManualChunk）。V2.0+ 可透過 read replica 分擔讀取負載。pgvector HNSW 索引在此規模下查詢延遲 < 10ms。
    - **Redis:** V1.0 單節點，預估 Session 數量 < 1000，記憶體需求 < 512MB。V2.0+ 若需高可用可升級至 Redis Sentinel。
    - **Google AI API:** 需監控 API 配額（QPM/TPM），設定用量上限。若超過免費額度，需規劃付費方案預算。
    - **LINE Messaging API:** Push Message 有免費額度限制（每月 500 則），超過需購買加值方案。需監控每月 Push Message 使用量。

### G.4 可維護性與文檔 (Maintainability & Documentation)

*   `[x]` **部署文檔/腳本 (Runbook/Playbook):**
    - 維護以下 Runbook 文檔：

      | Runbook | 內容 |
      |:---|:---|
      | **部署 Runbook** | Docker Compose 部署步驟、環境變數配置、SSL 證書設定、Nginx 配置 |
      | **回滾 Runbook** | 如何回滾至前一版本（`docker-compose pull` 指定版本 tag, `docker-compose up -d`） |
      | **備份恢復 Runbook** | PostgreSQL 備份恢復完整步驟（含解密、恢復、驗證） |
      | **故障排查 Runbook** | 常見故障場景診斷步驟：API 500 錯誤、LLM 不可達、Redis 連線失敗、資料庫連線耗盡 |
      | **密鑰輪替 Runbook** | 各項密鑰的輪替步驟與驗證方法 |
      | **安全事件應急 Runbook** | 資料外洩、API Key 洩露、DDoS 攻擊的應急回應流程 |

    - 所有 Runbook 存放於 `docs/runbooks/` 目錄，與程式碼一同版本控制。

*   `[x]` **CI/CD:**
    - 已建立 GitHub Actions CI/CD Pipeline：

      | 階段 | 觸發條件 | 執行內容 | 失敗處理 |
      |:---|:---|:---|:---|
      | **Lint** | PR / Push | `ruff check`, `mypy` 型別檢查 | 阻擋 PR merge |
      | **Security Scan** | PR / Push | `pip-audit`, `gitleaks`, `trivy` | 阻擋 PR merge |
      | **Test** | PR / Push | `pytest` 單元/整合測試，覆蓋率 >= 70% | 阻擋 PR merge |
      | **Build** | PR / Push | `docker build` 驗證 | 阻擋 PR merge |
      | **Tag** | Merge to main | Semantic Version Git Tag | 手動介入 |
      | **Push Image** | Tag created | 推送至 Container Registry | 重試 3 次 |
      | **Deploy** | Image pushed | `docker-compose pull && docker-compose up -d` | 回滾至前一版本 |
      | **Smoke Test** | Deploy completed | `/health` 端點驗證 + 關鍵 API 驗證 | 自動回滾 + 告警 |

*   `[x]` **配置管理 (Configuration Management):**
    - 所有服務配置透過環境變數管理（Docker Compose `env_file` 注入），不硬編碼於程式碼或鏡像中。
    - 環境變數清單定義於 `docs/05_architecture_and_design_document.md` 附錄 C。
    - 每個環境（dev/staging/prod）使用獨立的 `.env` 檔案。
    - 提供 `.env.example` 範本供開發者參考。
    - 應用層配置（如 `VECTOR_SIMILARITY_THRESHOLD`, `SESSION_TTL_SECONDS`, `MAX_CONVERSATION_TURNS`）可透過環境變數調整，無需重新建置鏡像。
    - LLM System Prompt Templates 存放於 `configs/prompts/` 目錄，可獨立於程式碼更新。

*   `[x]` **功能開關 (Feature Flags):**
    - 為以下有風險的功能設計功能開關（環境變數 or Redis key）：

      | 功能開關 | 預設值 | 用途 |
      |:---|:---|:---|
      | `ENABLE_L2_RAG` | `true` | 啟用/停用 L2 RAG Pipeline（停用時跳過 L2 直接進 L3） |
      | `ENABLE_SOP_AUTO_GENERATION` | `true` | 啟用/停用 SOP 自動生成（停用時不觸發 LLM 草擬 SOP） |
      | `ENABLE_CONTENT_FILTER` | `true` | 啟用/停用不當內容過濾層 |
      | `ENABLE_PROMPT_INJECTION_DETECTION` | `true` | 啟用/停用 Prompt Injection 偵測層 |
      | `ENABLE_IMAGE_ANALYSIS` | `true` | 啟用/停用 Vision AI 圖片分析 |
      | `ENABLE_DISPATCH_AUTO_MATCH` (V2.0) | `true` | 啟用/停用自動派工匹配（停用時僅支援手動指派） |
      | `ENABLE_PUSH_NOTIFICATION` (V2.0) | `true` | 啟用/停用 LINE Push Notification |

    - 功能開關可在運行時透過修改 Redis key 即時生效，無需重啟服務。
    - 生產環境出現異常時可快速停用特定功能進行隔離排查。

---

**文件審核記錄 (Review History):**

| 日期 | 審核人 | 版本 | 變更摘要 |
| :--- | :--- | :--- | :--- |
| 2026-02-25 | 技術架構師 | v1.0 | 初稿完成，涵蓋 V1.0 + V2.0 全面安全與生產準備就緒檢查清單 |
