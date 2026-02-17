# 專案結構指南 - 電子鎖智能客服與派工平台

**文件版本:** v1.0
**最後更新:** 2026-02-17
**主要作者:** 技術負責人
**狀態:** 活躍 (Active)

---

## 目錄

- [1. 指南目的](#1-指南目的)
- [2. 核心設計原則](#2-核心設計原則)
- [3. 頂層目錄結構](#3-頂層目錄結構)
- [4. 後端目錄詳解 (backend/)](#4-後端目錄詳解-backend)
  - [4.1 src/smart\_lock/ - 應用程式原始碼](#41-srcsmart_lock---應用程式原始碼)
  - [4.2 tests/ - 測試代碼](#42-tests---測試代碼)
  - [4.3 alembic/ - 資料庫遷移](#43-alembic---資料庫遷移)
- [5. 前端目錄詳解 (frontend/) - V2.0](#5-前端目錄詳解-frontend---v20)
  - [5.1 src/app/ - Next.js App Router](#51-srcapp---nextjs-app-router)
  - [5.2 src/components/ - 共用元件](#52-srccomponents---共用元件)
  - [5.3 src/lib/ - 工具函式與 API 客戶端](#53-srclib---工具函式與-api-客戶端)
- [6. Docker 與部署結構](#6-docker-與部署結構)
  - [6.1 docker-compose.yml 服務定義](#61-docker-composeyml-服務定義)
  - [6.2 .github/workflows/](#62-githubworkflows)
- [7. 設定檔結構](#7-設定檔結構)
- [8. 檔案命名約定](#8-檔案命名約定)
- [9. 演進原則](#9-演進原則)

---

## 1. 指南目的

本指南為「電子鎖智能客服與派工 SaaS 平台」提供標準化、可擴展且易於理解的目錄與檔案結構規範。具體目標：

- **新人快速上手：** 任何新加入的開發者閱讀本文件後，應能在 30 分鐘內定位任何模組的程式碼位置。
- **一致性保障：** 團隊成員在新增功能或模組時，遵循統一的組織方式，避免結構混亂。
- **關注點分離：** 透過 Clean Architecture 分層，確保領域邏輯不依賴基礎設施細節，提高可測試性與可維護性。
- **版本演進可控：** V1.0（LINE Bot + Admin API）與 V2.0（技師工作台 + 派工/報價/對帳）的目錄結構能平滑過渡，無需大幅重構。

---

## 2. 核心設計原則

### 2.1 按領域/功能組織 (Organize by Domain/Feature)

相關的業務功能（對話管理、問題卡、知識庫、派工等）應集中在同一目錄下，而非按技術類型（controllers、models、services）分散。這確保修改某個業務功能時，變更範圍侷限在單一目錄內。

```
# 正確 - 按領域組織
domains/conversation/entities.py
domains/conversation/events.py
domains/problem_card/entities.py

# 錯誤 - 按類型組織
models/conversation.py
models/problem_card.py
controllers/conversation.py
controllers/problem_card.py
```

### 2.2 Clean Architecture 分層

每個業務領域橫跨三層，依賴方向由外向內：

```
Infrastructure (外層) --> Application (中層) --> Domain (內層)
```

- **Domain Layer：** 純業務邏輯，零外部依賴。包含 entities、value objects、domain events。
- **Application Layer：** 編排業務流程。包含 use cases、DTOs、validators。依賴 Domain Layer。
- **Infrastructure Layer：** 與外部世界交互。包含 web routers、repositories、external API clients。依賴 Application Layer。

### 2.3 設定外部化 (Configuration Externalization)

所有環境相關設定（資料庫連線、API Key、LINE Channel Secret 等）透過環境變數或 `configs/` 目錄下的設定檔載入，絕不寫死在程式碼中。

### 2.4 根目錄簡潔 (Clean Root Directory)

專案根目錄只放專案級別的設定檔（`README.md`、`docker-compose.yml`、`.gitignore` 等），所有原始碼位於 `backend/` 和 `frontend/` 子目錄中。

### 2.5 可預測性 (Predictability)

看到領域名稱就能推斷出檔案位置。例如：知道有個「問題卡」功能，就能預測以下路徑存在：

- `backend/src/smart_lock/domains/problem_card/entities.py`
- `backend/src/smart_lock/application/problem_card/use_cases.py`
- `backend/src/smart_lock/infrastructure/web/routers/problem_cards.py`
- `backend/tests/features/problem_card/`

---

## 3. 頂層目錄結構

```plaintext
smart-lock-platform/                    # 專案根目錄
│
├── .github/                            # GitHub 相關設定
│   └── workflows/                      # GitHub Actions CI/CD 工作流程
│       ├── ci.yml                      #   Lint + 測試（每次 push/PR 觸發）
│       └── deploy.yml                  #   建置 + 部署（merge 到 main 時觸發）
│
├── backend/                            # Python 後端（FastAPI）
│   ├── src/                            #   應用程式原始碼
│   │   └── smart_lock/                 #     主應用程式 Python package
│   ├── tests/                          #   測試代碼
│   ├── alembic/                        #   資料庫遷移（Alembic）
│   ├── alembic.ini                     #   Alembic 設定檔
│   ├── pyproject.toml                  #   Python 專案定義與依賴（Poetry）
│   ├── poetry.lock                     #   Poetry 鎖定檔
│   └── Dockerfile                      #   後端容器映像檔定義
│
├── frontend/                           # Next.js 前端（V2.0 新增）
│   ├── src/                            #   前端原始碼
│   ├── public/                         #   靜態資源
│   ├── package.json                    #   Node.js 專案定義
│   ├── package-lock.json               #   依賴鎖定檔
│   ├── tsconfig.json                   #   TypeScript 設定
│   ├── next.config.js                  #   Next.js 設定
│   ├── tailwind.config.ts              #   Tailwind CSS 設定
│   └── Dockerfile                      #   前端容器映像檔定義
│
├── configs/                            # 外部化設定檔
│   ├── settings.toml                   #   應用程式設定（非機密）
│   ├── prompts/                        #   LLM System Prompts 模板
│   │   ├── intent_recognition.txt      #     意圖辨識 prompt
│   │   ├── ner_extraction.txt          #     NER 實體擷取 prompt
│   │   ├── problem_card_gen.txt        #     問題卡自動生成 prompt
│   │   ├── rag_answer.txt              #     RAG 回答生成 prompt
│   │   ├── sop_draft.txt               #     SOP 草稿自動撰寫 prompt
│   │   └── content_filter.txt          #     內容安全過濾 prompt
│   └── logging.conf                    #   日誌設定
│
├── data/                               # 靜態資料與種子資料
│   ├── seed/                           #   資料庫初始種子資料
│   │   ├── lock_models.json            #     電子鎖型號主檔
│   │   ├── fault_codes.json            #     標準故障代碼表
│   │   └── default_faq.json            #     預設 FAQ 問答
│   └── manuals/                        #   電子鎖操作手冊 PDF（供 RAG ingestion）
│
├── scripts/                            # 開發與運維腳本
│   ├── setup_dev.sh                    #   開發環境一鍵安裝
│   ├── seed_database.py                #   種子資料匯入
│   ├── ingest_manuals.py               #   手冊 PDF 切片與向量化匯入
│   ├── run_migrations.sh               #   執行資料庫遷移
│   └── generate_api_client.sh          #   從 OpenAPI spec 生成前端 API client
│
├── docs/                               # 專案文件
│   ├── adrs/                           #   架構決策記錄 (Architecture Decision Records)
│   │   └── adr-001-backend-framework.md
│   ├── design/                         #   設計文件
│   ├── api/                            #   API 規格文件
│   └── images/                         #   文件中使用的圖片
│
├── nginx/                              # Nginx 反向代理設定
│   ├── nginx.conf                      #   主設定檔
│   └── conf.d/                         #   站台設定
│       └── default.conf                #     路由規則（/api -> backend, / -> frontend）
│
├── docker-compose.yml                  # 容器編排定義（開發環境）
├── docker-compose.prod.yml             # 容器編排定義（生產環境）
├── .env.example                        # 環境變數範本（已納入 Git）
├── .gitignore                          # Git 忽略規則
├── .pre-commit-config.yaml             # pre-commit 鉤子設定
├── Makefile                            # 常用指令快捷方式
├── LICENSE                             # 授權條款
└── README.md                           # 專案介紹與快速入門
```

---

## 4. 後端目錄詳解 (backend/)

### 4.1 src/smart_lock/ - 應用程式原始碼

此為後端核心，採用 Clean Architecture 分層組織。所有業務功能分布在 `domains/`、`application/`、`infrastructure/` 三層中。

```plaintext
backend/src/smart_lock/
│
├── __init__.py                         # Package 標識，包含版本號
├── main.py                             # FastAPI 應用程式入口點
│                                       #   - 建立 FastAPI instance
│                                       #   - 註冊所有 routers
│                                       #   - 設定 middleware (CORS, logging, error handling)
│                                       #   - 定義 lifespan 事件 (startup/shutdown)
│
├── core/                               # ── 核心共用模組 ──
│   ├── __init__.py
│   ├── config.py                       # 設定載入（讀取環境變數 + settings.toml）
│   │                                   #   - Settings class (Pydantic BaseSettings)
│   │                                   #   - Database URL, Redis URL
│   │                                   #   - LINE Channel Secret/Token
│   │                                   #   - OpenAI API Key, model name
│   │                                   #   - 各環境參數 (dev/staging/prod)
│   ├── security.py                     # 安全模組
│   │                                   #   - JWT token 生成與驗證
│   │                                   #   - LINE Webhook 簽章驗證
│   │                                   #   - 密碼雜湊 (bcrypt)
│   │                                   #   - Prompt injection 防禦邏輯
│   ├── dependencies.py                 # FastAPI Dependency Injection
│   │                                   #   - get_db_session() -> AsyncSession
│   │                                   #   - get_redis_client() -> Redis
│   │                                   #   - get_current_user() -> AdminUser
│   │                                   #   - get_openai_client() -> AsyncOpenAI
│   │                                   #   - get_line_client() -> LineBotApi
│   ├── exceptions.py                   # 全域例外定義
│   │                                   #   - AppException (base)
│   │                                   #   - NotFoundError
│   │                                   #   - ValidationError
│   │                                   #   - AuthenticationError
│   │                                   #   - ExternalServiceError
│   │                                   #   - ContentFilterError
│   ├── middleware.py                    # 自訂 Middleware
│   │                                   #   - RequestLoggingMiddleware
│   │                                   #   - ErrorHandlingMiddleware
│   │                                   #   - RateLimitMiddleware
│   └── constants.py                    # 全域常數
│                                       #   - SessionState enum
│                                       #   - ProblemCardStatus enum
│                                       #   - ResolutionLayer enum
│                                       #   - WorkOrderStatus enum (V2.0)
│
├── domains/                            # ── 領域模型層 (Domain Layer) ──
│   ├── __init__.py                     #   純業務邏輯，零外部依賴
│   │
│   ├── conversation/                   # 對話管理領域
│   │   ├── __init__.py
│   │   ├── entities.py                 #   - Conversation: 對話 session 實體
│   │   │                               #   - Message: 單則訊息（含角色、內容、時間戳）
│   │   │                               #   - ConversationContext: 多輪對話上下文
│   │   ├── value_objects.py            #   - SessionId: 會話識別碼
│   │   │                               #   - MessageRole: USER / ASSISTANT / SYSTEM
│   │   │                               #   - ChannelType: LINE / WEB / API
│   │   └── events.py                   #   - ConversationStarted
│   │                                   #   - MessageReceived
│   │                                   #   - ConversationEscalated (轉人工)
│   │                                   #   - ConversationClosed
│   │
│   ├── problem_card/                   # 問題卡引擎領域
│   │   ├── __init__.py
│   │   ├── entities.py                 #   - ProblemCard: 結構化診斷卡實體
│   │   │                               #     (lock_model, fault_symptom, error_code,
│   │   │                               #      user_description, environment_info,
│   │   │                               #      confidence_score, status)
│   │   │                               #   - ProblemCardHistory: 問題卡修改歷程
│   │   └── value_objects.py            #   - LockModel: 電子鎖型號值物件
│   │                                   #   - FaultSymptom: 故障症狀分類
│   │                                   #   - ErrorCode: 標準錯誤代碼
│   │                                   #   - ConfidenceScore: 信心分數 (0.0~1.0)
│   │
│   ├── knowledge_base/                 # 知識庫領域
│   │   ├── __init__.py
│   │   ├── entities.py                 #   - CaseEntry: 案例庫條目
│   │   │                               #     (title, symptoms, solution_steps,
│   │   │                               #      lock_models, success_rate, embedding)
│   │   │                               #   - ManualChunk: 手冊分片（PDF 切片後的文本塊）
│   │   │                               #     (source_pdf, page_range, content,
│   │   │                               #      chunk_index, embedding)
│   │   │                               #   - FAQEntry: 常見問答
│   │   │                               #   - SOPDraft: 自進化 SOP 草稿
│   │   │                               #     (trigger_problem_card, drafted_steps,
│   │   │                               #      review_status, adopted_as_case_id)
│   │   └── value_objects.py            #   - EmbeddingVector: 向量嵌入值物件
│   │                                   #   - ReviewStatus: PENDING / APPROVED / REJECTED
│   │                                   #   - ChunkMetadata: 分片元資料
│   │
│   ├── resolution/                     # 三層解析引擎領域
│   │   ├── __init__.py
│   │   ├── entities.py                 #   - ResolutionAttempt: 解析嘗試紀錄
│   │   │                               #     (layer, query, result, success, duration)
│   │   │                               #   - ResolutionResult: 最終解析結果
│   │   │                               #     (answer, source_references, confidence,
│   │   │                               #      resolution_layer, needs_escalation)
│   │   ├── value_objects.py            #   - ResolutionLayer: CASE_LIBRARY / RAG / HUMAN
│   │   │                               #   - SourceReference: 引用來源標記
│   │   └── strategies.py              #   - ResolutionStrategy (Protocol/ABC)
│   │                                   #   - CaseLibraryStrategy: 案例庫向量搜尋
│   │                                   #   - RAGStrategy: PDF 手冊 RAG pipeline
│   │                                   #   - HumanHandoffStrategy: 人工轉接
│   │
│   ├── dispatch/                       # 派工引擎領域（V2.0）
│   │   ├── __init__.py
│   │   ├── entities.py                 #   - WorkOrder: 派工單實體
│   │   │                               #     (problem_card_id, technician_id, status,
│   │   │                               #      scheduled_time, actual_arrival, completion)
│   │   │                               #   - Technician: 技師實體
│   │   │                               #     (name, skills, certifications,
│   │   │                               #      current_location, availability, rating)
│   │   │                               #   - DispatchMatch: 派工匹配結果
│   │   └── value_objects.py            #   - WorkOrderStatus: PENDING / ASSIGNED / IN_PROGRESS
│   │                                   #     / COMPLETED / CANCELLED
│   │                                   #   - TechnicianSkill: 技師技能認證
│   │                                   #   - GeoLocation: 經緯度座標
│   │                                   #   - ServiceArea: 服務區域
│   │
│   ├── pricing/                        # 報價引擎領域（V2.0）
│   │   ├── __init__.py
│   │   ├── entities.py                 #   - PriceRule: 定價規則實體
│   │   │                               #     (service_type, lock_model, base_price,
│   │   │                               #      urgency_multiplier, distance_surcharge)
│   │   │                               #   - Quotation: 報價單實體
│   │   │                               #     (work_order_id, line_items, total,
│   │   │                               #      valid_until, accepted)
│   │   └── value_objects.py            #   - ServiceType: INSTALL / REPAIR / MAINTENANCE / UNLOCK
│   │                                   #   - PriceComponent: 報價項目明細
│   │                                   #   - Money: 金額值物件（含幣別）
│   │
│   └── accounting/                     # 對帳系統領域（V2.0）
│       ├── __init__.py
│       ├── entities.py                 #   - Reconciliation: 對帳紀錄
│       │                               #     (period, technician_id, work_orders,
│       │                               #      total_amount, adjustments, status)
│       │                               #   - Settlement: 結算紀錄
│       │                               #     (reconciliation_id, payee, amount,
│       │                               #      payment_method, settled_at)
│       │                               #   - Voucher: 憑證/傳票
│       │                               #     (type, debit_account, credit_account,
│       │                               #      amount, reference_id)
│       └── value_objects.py            #   - ReconciliationStatus: DRAFT / CONFIRMED / SETTLED
│                                       #   - AccountCode: 會計科目代碼
│                                       #   - Period: 對帳期間（年/月）
│
├── application/                        # ── 應用邏輯層 (Application Layer) ──
│   ├── __init__.py                     #   編排業務流程，不包含基礎設施細節
│   │
│   ├── conversation/                   # 對話管理應用邏輯
│   │   ├── __init__.py
│   │   ├── use_cases.py                #   - StartConversationUseCase
│   │   │                               #   - ProcessMessageUseCase（核心：接收訊息 -> 意圖辨識
│   │   │                               #     -> NER 擷取 -> 問題卡更新 -> 觸發解析引擎 -> 回覆）
│   │   │                               #   - GetConversationHistoryUseCase
│   │   │                               #   - EscalateToHumanUseCase
│   │   │                               #   - CloseConversationUseCase
│   │   ├── dtos.py                     #   - IncomingMessageDTO
│   │   │                               #   - ConversationResponseDTO
│   │   │                               #   - ConversationListDTO
│   │   └── interfaces.py              #   - ConversationRepository (Protocol)
│   │                                   #   - MessageBroker (Protocol)
│   │
│   ├── problem_card/                   # 問題卡應用邏輯
│   │   ├── __init__.py
│   │   ├── use_cases.py                #   - GenerateProblemCardUseCase（LLM 自動生成）
│   │   │                               #   - UpdateProblemCardUseCase
│   │   │                               #   - GetProblemCardUseCase
│   │   │                               #   - ListProblemCardsUseCase
│   │   ├── dtos.py                     #   - ProblemCardCreateDTO
│   │   │                               #   - ProblemCardUpdateDTO
│   │   │                               #   - ProblemCardResponseDTO
│   │   └── interfaces.py              #   - ProblemCardRepository (Protocol)
│   │
│   ├── knowledge_base/                 # 知識庫應用邏輯
│   │   ├── __init__.py
│   │   ├── use_cases.py                #   - SearchCaseLibraryUseCase（向量相似度搜尋）
│   │   │                               #   - CreateCaseEntryUseCase
│   │   │                               #   - UpdateCaseEntryUseCase
│   │   │                               #   - IngestManualUseCase（PDF 切片 + 向量化）
│   │   │                               #   - ManageFAQUseCase
│   │   │                               #   - DraftSOPUseCase（自進化：自動產生 SOP 草稿）
│   │   │                               #   - ReviewSOPDraftUseCase（管理員審核）
│   │   │                               #   - AdoptSOPAsCaseUseCase（採納為正式案例）
│   │   ├── dtos.py                     #   - CaseEntryCreateDTO / CaseEntryResponseDTO
│   │   │                               #   - ManualChunkDTO
│   │   │                               #   - SOPDraftDTO / SOPReviewDTO
│   │   │                               #   - KBSearchQueryDTO / KBSearchResultDTO
│   │   └── interfaces.py              #   - CaseRepository (Protocol)
│   │                                   #   - ManualChunkRepository (Protocol)
│   │                                   #   - VectorSearchService (Protocol)
│   │
│   ├── resolution/                     # 三層解析引擎應用邏輯
│   │   ├── __init__.py
│   │   ├── use_cases.py                #   - ResolveQueryUseCase
│   │   │                               #     核心流程：
│   │   │                               #     1. Layer 1 - 案例庫向量搜尋
│   │   │                               #        -> 命中且信心分數 >= 閾值 -> 回傳結果
│   │   │                               #     2. Layer 2 - PDF 手冊 RAG pipeline
│   │   │                               #        -> 生成回答且品質合格 -> 回傳結果
│   │   │                               #     3. Layer 3 - 人工轉接
│   │   │                               #        -> 建立轉接工單，通知客服人員
│   │   │                               #   - GetResolutionHistoryUseCase
│   │   ├── dtos.py                     #   - ResolutionQueryDTO
│   │   │                               #   - ResolutionResultDTO
│   │   └── interfaces.py              #   - ResolutionStrategyPort (Protocol)
│   │
│   ├── auth/                           # 認證與授權應用邏輯
│   │   ├── __init__.py
│   │   ├── use_cases.py                #   - LoginUseCase
│   │   │                               #   - RefreshTokenUseCase
│   │   │                               #   - ChangePasswordUseCase
│   │   ├── dtos.py                     #   - LoginRequestDTO / TokenResponseDTO
│   │   └── interfaces.py              #   - UserRepository (Protocol)
│   │
│   ├── dashboard/                      # 管理後台儀表板應用邏輯
│   │   ├── __init__.py
│   │   ├── use_cases.py                #   - GetDashboardStatsUseCase
│   │   │                               #     (今日對話數、解析成功率、待處理工單、
│   │   │                               #      待審核 SOP 數量)
│   │   │                               #   - GetRecentConversationsUseCase
│   │   │                               #   - GetSystemHealthUseCase
│   │   └── dtos.py                     #   - DashboardStatsDTO
│   │                                   #   - SystemHealthDTO
│   │
│   ├── dispatch/                       # 派工引擎應用邏輯（V2.0）
│   │   ├── __init__.py
│   │   ├── use_cases.py                #   - CreateWorkOrderUseCase
│   │   │                               #   - MatchTechnicianUseCase（智慧匹配演算法）
│   │   │                               #   - AssignWorkOrderUseCase
│   │   │                               #   - UpdateWorkOrderStatusUseCase
│   │   │                               #   - ListTechnicianWorkOrdersUseCase
│   │   │                               #   - ManageTechnicianProfileUseCase
│   │   ├── dtos.py                     #   - WorkOrderCreateDTO / WorkOrderResponseDTO
│   │   │                               #   - TechnicianDTO / MatchResultDTO
│   │   └── interfaces.py              #   - WorkOrderRepository (Protocol)
│   │                                   #   - TechnicianRepository (Protocol)
│   │                                   #   - GeocodingService (Protocol)
│   │
│   ├── pricing/                        # 報價引擎應用邏輯（V2.0）
│   │   ├── __init__.py
│   │   ├── use_cases.py                #   - CalculateQuotationUseCase（規則式報價計算）
│   │   │                               #   - ManagePriceRuleUseCase
│   │   │                               #   - AcceptQuotationUseCase
│   │   ├── dtos.py                     #   - QuotationRequestDTO / QuotationResponseDTO
│   │   │                               #   - PriceRuleDTO
│   │   └── interfaces.py              #   - PriceRuleRepository (Protocol)
│   │
│   └── accounting/                     # 對帳系統應用邏輯（V2.0）
│       ├── __init__.py
│       ├── use_cases.py                #   - GenerateReconciliationUseCase（自動產生對帳單）
│       │                               #   - ConfirmReconciliationUseCase
│       │                               #   - ProcessSettlementUseCase
│       │                               #   - GenerateVoucherUseCase
│       │                               #   - GetAccountingReportUseCase
│       ├── dtos.py                     #   - ReconciliationDTO / SettlementDTO
│       │                               #   - VoucherDTO / AccountingReportDTO
│       └── interfaces.py              #   - ReconciliationRepository (Protocol)
│                                       #   - SettlementRepository (Protocol)
│                                       #   - PaymentGateway (Protocol)
│
├── infrastructure/                     # ── 基礎設施層 (Infrastructure Layer) ──
│   ├── __init__.py                     #   與外部世界交互的所有實作
│   │
│   ├── web/                            # Web 框架相關（FastAPI Routers）
│   │   ├── __init__.py
│   │   └── routers/                    # API 路由定義
│   │       ├── __init__.py
│   │       ├── webhook.py              #   POST /webhook/line
│   │       │                           #     接收 LINE Messaging API 事件
│   │       │                           #     驗證 X-Line-Signature
│   │       │                           #     立即回應 HTTP 200
│   │       │                           #     以 BackgroundTask 非同步處理訊息
│   │       ├── conversations.py        #   GET  /api/v1/conversations
│   │       │                           #   GET  /api/v1/conversations/{id}
│   │       │                           #   POST /api/v1/conversations/{id}/escalate
│   │       │                           #   POST /api/v1/conversations/{id}/close
│   │       ├── problem_cards.py        #   GET  /api/v1/problem-cards
│   │       │                           #   GET  /api/v1/problem-cards/{id}
│   │       │                           #   PUT  /api/v1/problem-cards/{id}
│   │       │                           #   GET  /api/v1/problem-cards/{id}/history
│   │       ├── knowledge_base.py       #   GET  /api/v1/knowledge-base/cases
│   │       │                           #   POST /api/v1/knowledge-base/cases
│   │       │                           #   PUT  /api/v1/knowledge-base/cases/{id}
│   │       │                           #   DELETE /api/v1/knowledge-base/cases/{id}
│   │       │                           #   POST /api/v1/knowledge-base/search
│   │       │                           #   GET  /api/v1/knowledge-base/faq
│   │       │                           #   POST /api/v1/knowledge-base/faq
│   │       ├── manuals.py              #   POST /api/v1/manuals/ingest  (上傳 PDF 並切片)
│   │       │                           #   GET  /api/v1/manuals
│   │       │                           #   GET  /api/v1/manuals/{id}/chunks
│   │       ├── sop_drafts.py           #   GET  /api/v1/sop-drafts
│   │       │                           #   GET  /api/v1/sop-drafts/{id}
│   │       │                           #   POST /api/v1/sop-drafts/{id}/approve
│   │       │                           #   POST /api/v1/sop-drafts/{id}/reject
│   │       │                           #   POST /api/v1/sop-drafts/{id}/adopt
│   │       ├── auth.py                 #   POST /api/v1/auth/login
│   │       │                           #   POST /api/v1/auth/refresh
│   │       │                           #   POST /api/v1/auth/change-password
│   │       ├── dashboard.py            #   GET  /api/v1/dashboard/stats
│   │       │                           #   GET  /api/v1/dashboard/recent
│   │       │                           #   GET  /api/v1/dashboard/health
│   │       ├── config_admin.py         #   GET  /api/v1/config  (系統參數管理)
│   │       │                           #   PUT  /api/v1/config
│   │       ├── work_orders.py          #   V2.0 - 派工單 CRUD + 狀態更新
│   │       ├── technicians.py          #   V2.0 - 技師管理 + 可用性查詢
│   │       ├── quotations.py           #   V2.0 - 報價單 CRUD
│   │       ├── price_rules.py          #   V2.0 - 定價規則管理
│   │       └── accounting.py           #   V2.0 - 對帳/結算/憑證
│   │
│   ├── persistence/                    # 持久化層（資料庫相關）
│   │   ├── __init__.py
│   │   ├── database.py                 #   AsyncEngine / AsyncSessionLocal 建立
│   │   │                               #   SQLAlchemy 2.0 async session 工廠
│   │   ├── base_model.py              #   ORM Base class（含 id, created_at, updated_at）
│   │   ├── orm_models/                 #   SQLAlchemy ORM 模型（對應 DB tables）
│   │   │   ├── __init__.py
│   │   │   ├── conversation_model.py   #     conversations, messages tables
│   │   │   ├── problem_card_model.py   #     problem_cards, problem_card_histories tables
│   │   │   ├── knowledge_base_model.py #     case_entries, manual_chunks, faq_entries tables
│   │   │   ├── sop_draft_model.py      #     sop_drafts table
│   │   │   ├── resolution_model.py     #     resolution_attempts table
│   │   │   ├── user_model.py           #     admin_users table
│   │   │   ├── work_order_model.py     #     V2.0 - work_orders table
│   │   │   ├── technician_model.py     #     V2.0 - technicians, technician_skills tables
│   │   │   ├── pricing_model.py        #     V2.0 - price_rules, quotations tables
│   │   │   └── accounting_model.py     #     V2.0 - reconciliations, settlements, vouchers
│   │   └── repositories/              #   Repository 實作（實作 application 層的 Protocol）
│   │       ├── __init__.py
│   │       ├── conversation_repo.py
│   │       ├── problem_card_repo.py
│   │       ├── case_repo.py            #     含 pgvector 向量搜尋實作
│   │       ├── manual_chunk_repo.py    #     含 pgvector 向量搜尋實作
│   │       ├── sop_draft_repo.py
│   │       ├── user_repo.py
│   │       ├── work_order_repo.py      #     V2.0
│   │       ├── technician_repo.py      #     V2.0
│   │       ├── price_rule_repo.py      #     V2.0
│   │       └── accounting_repo.py      #     V2.0
│   │
│   ├── external/                       # 外部服務客戶端
│   │   ├── __init__.py
│   │   ├── line_client.py              #   LINE Messaging API 封裝
│   │   │                               #     - send_text_message()
│   │   │                               #     - send_flex_message() (問題卡/報價呈現)
│   │   │                               #     - send_quick_reply()
│   │   │                               #     - get_user_profile()
│   │   ├── openai_client.py            #   OpenAI API 封裝
│   │   │                               #     - chat_completion() (async)
│   │   │                               #     - create_embedding() (async)
│   │   │                               #     - content_moderation() (async)
│   │   ├── langchain_chains/           #   LangChain chain 定義
│   │   │   ├── __init__.py
│   │   │   ├── intent_chain.py         #     意圖辨識 chain
│   │   │   ├── ner_chain.py            #     NER 實體擷取 chain
│   │   │   ├── problem_card_chain.py   #     問題卡自動生成 chain
│   │   │   ├── rag_chain.py            #     RAG 問答 chain（RetrievalQA）
│   │   │   ├── sop_draft_chain.py      #     SOP 自動撰寫 chain
│   │   │   └── content_filter_chain.py #     內容安全過濾 chain
│   │   └── geocoding_client.py         #   V2.0 - 地理編碼服務（技師定位）
│   │
│   └── cache/                          # 快取層（Redis）
│       ├── __init__.py
│       ├── redis_client.py             #   Redis 連線管理
│       ├── session_store.py            #   對話 session 狀態快取
│       │                               #     - 儲存多輪對話的暫存上下文
│       │                               #     - Session TTL 管理
│       │                               #     - 問題卡暫存（生成中的草稿）
│       └── rate_limiter.py             #   API 請求頻率限制
│
└── py.typed                            # PEP 561 typed package marker
```

#### 4.1.1 core/ - 核心共用模組

`core/` 放置跨領域共用的基礎設施，所有其他模組都可能依賴此處的程式碼。

| 檔案 | 職責 | 關鍵類別/函式 |
|------|------|--------------|
| `config.py` | 從環境變數 + `settings.toml` 載入設定 | `Settings(BaseSettings)` |
| `security.py` | 認證授權與安全防護 | `verify_line_signature()`, `create_jwt()`, `verify_jwt()`, `detect_prompt_injection()` |
| `dependencies.py` | FastAPI DI 提供者 | `get_db_session()`, `get_redis_client()`, `get_current_user()` |
| `exceptions.py` | 全域例外階層 | `AppException`, `NotFoundError`, `AuthenticationError` |
| `middleware.py` | HTTP 中介層 | `RequestLoggingMiddleware`, `ErrorHandlingMiddleware` |
| `constants.py` | 列舉值與常數 | `SessionState`, `ProblemCardStatus`, `ResolutionLayer` |

#### 4.1.2 domains/ - 領域模型層

此層是系統的核心，包含純業務規則。**嚴格禁止**在此層引入任何框架依賴（不可 import FastAPI、SQLAlchemy、Redis 等）。

**V1.0 領域：**

| 領域 | 核心實體 | 業務規則 |
|------|---------|---------|
| `conversation/` | Conversation, Message | 多輪對話狀態機、上下文視窗管理、轉接判斷邏輯 |
| `problem_card/` | ProblemCard | 問題卡欄位完整度計算、信心分數邏輯、狀態流轉 |
| `knowledge_base/` | CaseEntry, ManualChunk, SOPDraft | 案例匹配分數計算、SOP 草稿生命週期管理 |
| `resolution/` | ResolutionAttempt, ResolutionResult | 三層引擎策略選擇、信心閾值判斷、降級邏輯 |

**V2.0 新增領域：**

| 領域 | 核心實體 | 業務規則 |
|------|---------|---------|
| `dispatch/` | WorkOrder, Technician, DispatchMatch | 技師匹配演算法（技能 + 距離 + 可用性）、工單狀態機 |
| `pricing/` | PriceRule, Quotation | 報價計算規則引擎、急件加成、距離附加費 |
| `accounting/` | Reconciliation, Settlement, Voucher | 對帳期間彙總、結算金額計算、複式記帳憑證 |

#### 4.1.3 application/ - 應用邏輯層

此層編排 domain entities 完成業務流程。每個 use case 是一個獨立的操作單元。

**關鍵設計：**

- 每個 use case class 只有一個公開方法 `execute()`，接收 DTO、回傳 DTO。
- 透過 `interfaces.py` 中定義的 Protocol，宣告對 Repository 的依賴（依賴反轉）。
- 此層不直接操作資料庫或呼叫外部 API，一切透過 Protocol 抽象。

```python
# 範例：application/resolution/use_cases.py
class ResolveQueryUseCase:
    def __init__(
        self,
        case_repo: CaseRepository,        # Protocol
        chunk_repo: ManualChunkRepository, # Protocol
        llm_client: LLMService,           # Protocol
    ):
        self._case_repo = case_repo
        self._chunk_repo = chunk_repo
        self._llm = llm_client

    async def execute(self, query: ResolutionQueryDTO) -> ResolutionResultDTO:
        # Layer 1: Case library vector search
        # Layer 2: RAG pipeline
        # Layer 3: Human handoff
        ...
```

#### 4.1.4 infrastructure/ - 基礎設施層

此層是所有外部世界交互的實作所在。分為四大區塊：

| 區塊 | 職責 | 依賴的外部技術 |
|------|------|--------------|
| `web/routers/` | HTTP API 端點定義、請求/回應處理 | FastAPI |
| `persistence/` | 資料庫存取、ORM 模型、遷移 | SQLAlchemy 2.0, asyncpg, pgvector |
| `external/` | 第三方 API 客戶端 | LINE SDK, OpenAI SDK, LangChain |
| `cache/` | 快取與 session 管理 | Redis (aioredis) |

### 4.2 tests/ - 測試代碼

測試目錄結構鏡射 `src/smart_lock/` 的組織方式，方便定位。

```plaintext
backend/tests/
│
├── __init__.py
├── conftest.py                         # 全域 pytest fixtures
│                                       #   - async_session fixture (test DB)
│                                       #   - redis_client fixture (test Redis)
│                                       #   - test_client fixture (FastAPI TestClient)
│                                       #   - mock_openai_client fixture
│                                       #   - mock_line_client fixture
│                                       #   - sample_problem_card fixture
├── factories.py                        # 測試資料工廠（factory-boy）
│                                       #   - ConversationFactory
│                                       #   - ProblemCardFactory
│                                       #   - CaseEntryFactory
│                                       #   - WorkOrderFactory (V2.0)
│                                       #   - TechnicianFactory (V2.0)
│
├── unit/                               # 單元測試（不依賴外部服務）
│   ├── __init__.py
│   ├── domains/                        # Domain Layer 測試
│   │   ├── test_conversation_entities.py
│   │   ├── test_problem_card_entities.py
│   │   ├── test_knowledge_base_entities.py
│   │   ├── test_resolution_strategies.py
│   │   ├── test_dispatch_entities.py       # V2.0
│   │   ├── test_pricing_entities.py        # V2.0
│   │   └── test_accounting_entities.py     # V2.0
│   ├── application/                    # Application Layer 測試（mock repositories）
│   │   ├── test_process_message.py
│   │   ├── test_generate_problem_card.py
│   │   ├── test_resolve_query.py
│   │   ├── test_draft_sop.py
│   │   ├── test_match_technician.py        # V2.0
│   │   ├── test_calculate_quotation.py     # V2.0
│   │   └── test_generate_reconciliation.py # V2.0
│   └── core/
│       ├── test_security.py
│       └── test_config.py
│
├── integration/                        # 整合測試（使用 test DB / test Redis）
│   ├── __init__.py
│   ├── persistence/
│   │   ├── test_conversation_repo.py
│   │   ├── test_case_repo_vector_search.py # pgvector 向量搜尋測試
│   │   ├── test_problem_card_repo.py
│   │   └── test_work_order_repo.py         # V2.0
│   ├── external/
│   │   ├── test_openai_client.py       #   使用 mock/VCR cassettes
│   │   └── test_line_client.py
│   └── cache/
│       └── test_session_store.py
│
├── features/                           # 功能測試（端對端 API 測試）
│   ├── __init__.py
│   ├── test_webhook_flow.py            # LINE Webhook -> 對話 -> 解析 -> 回覆
│   ├── test_problem_card_api.py        # 問題卡 CRUD API
│   ├── test_knowledge_base_api.py      # 知識庫管理 API
│   ├── test_sop_review_flow.py         # SOP 草稿 -> 審核 -> 採納 流程
│   ├── test_auth_flow.py              # 登入 -> Token -> 受保護 API
│   ├── test_dispatch_flow.py           # V2.0 - 建單 -> 匹配 -> 派工 -> 完工
│   ├── test_pricing_flow.py            # V2.0 - 報價計算 -> 接受
│   └── test_accounting_flow.py         # V2.0 - 對帳 -> 結算 -> 憑證
│
└── fixtures/                           # 測試用靜態資料
    ├── sample_line_events.json         #   LINE Webhook event 範例
    ├── sample_problem_card.json        #   問題卡範例資料
    ├── sample_manual_chunk.txt         #   手冊文本分片範例
    └── sample_case_entries.json        #   案例庫測試資料
```

### 4.3 alembic/ - 資料庫遷移

使用 Alembic 管理 PostgreSQL schema 變更歷史。

```plaintext
backend/alembic/
│
├── env.py                              # Alembic 環境設定
│                                       #   - 載入 SQLAlchemy Base.metadata
│                                       #   - 設定 async migration 支援
├── script.py.mako                      # 遷移腳本模板
└── versions/                           # 遷移版本（按時間排序）
    ├── 001_create_conversations.py
    ├── 002_create_problem_cards.py
    ├── 003_create_knowledge_base.py
    ├── 004_add_pgvector_extension.py   #   啟用 pgvector，建立向量索引
    ├── 005_create_resolution_attempts.py
    ├── 006_create_admin_users.py
    ├── 007_create_sop_drafts.py
    ├── 010_create_work_orders.py       #   V2.0
    ├── 011_create_technicians.py       #   V2.0
    ├── 012_create_pricing.py           #   V2.0
    └── 013_create_accounting.py        #   V2.0
```

---

## 5. 前端目錄詳解 (frontend/) - V2.0

前端在 V2.0 階段新增，使用 Next.js 14+ App Router 架構，為管理後台與技師工作台提供 Web UI。

```plaintext
frontend/src/
│
├── app/                                # ── Next.js App Router ──
│   ├── layout.tsx                      # 根佈局（全域 providers, 字型, metadata）
│   ├── page.tsx                        # 首頁（重導向至 /dashboard）
│   ├── globals.css                     # 全域樣式（Tailwind base）
│   │
│   ├── (auth)/                         # 認證相關頁面（不含側邊欄佈局）
│   │   ├── layout.tsx                  #   認證頁面專用佈局（置中卡片）
│   │   ├── login/
│   │   │   └── page.tsx                #   登入頁
│   │   └── forgot-password/
│   │       └── page.tsx                #   忘記密碼頁
│   │
│   ├── (dashboard)/                    # 後台主區域（含側邊欄佈局）
│   │   ├── layout.tsx                  #   後台佈局（側邊欄 + 頂部導航 + 主內容區）
│   │   │
│   │   ├── dashboard/
│   │   │   └── page.tsx                #   儀表板首頁
│   │   │                               #     - 今日對話統計
│   │   │                               #     - AI 解析成功率趨勢
│   │   │                               #     - 待處理工單數
│   │   │                               #     - 待審核 SOP 提醒
│   │   │
│   │   ├── conversations/
│   │   │   ├── page.tsx                #   對話列表頁（搜尋、篩選、分頁）
│   │   │   └── [id]/
│   │   │       └── page.tsx            #   對話詳情頁（訊息時間軸、問題卡關聯）
│   │   │
│   │   ├── problem-cards/
│   │   │   ├── page.tsx                #   問題卡列表頁
│   │   │   └── [id]/
│   │   │       └── page.tsx            #   問題卡詳情/編輯頁
│   │   │
│   │   ├── knowledge-base/
│   │   │   ├── page.tsx                #   知識庫總覽
│   │   │   ├── cases/
│   │   │   │   ├── page.tsx            #   案例庫列表
│   │   │   │   ├── new/
│   │   │   │   │   └── page.tsx        #   新增案例
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx        #   案例詳情/編輯
│   │   │   ├── manuals/
│   │   │   │   ├── page.tsx            #   手冊管理（上傳 PDF、查看分片）
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx        #   手冊分片檢視
│   │   │   ├── faq/
│   │   │   │   └── page.tsx            #   FAQ 管理
│   │   │   └── sop-drafts/
│   │   │       ├── page.tsx            #   SOP 草稿待審列表
│   │   │       └── [id]/
│   │   │           └── page.tsx        #   SOP 草稿審核頁（核准/駁回/採納）
│   │   │
│   │   ├── work-orders/                # V2.0 - 派工管理
│   │   │   ├── page.tsx                #   工單列表（看板/列表雙視圖）
│   │   │   ├── new/
│   │   │   │   └── page.tsx            #   建立工單
│   │   │   └── [id]/
│   │   │       └── page.tsx            #   工單詳情（狀態追蹤、技師指派）
│   │   │
│   │   ├── technicians/                # V2.0 - 技師管理
│   │   │   ├── page.tsx                #   技師列表（含地圖檢視）
│   │   │   ├── new/
│   │   │   │   └── page.tsx            #   新增技師
│   │   │   └── [id]/
│   │   │       └── page.tsx            #   技師詳情（技能、排程、評分）
│   │   │
│   │   ├── accounting/                 # V2.0 - 對帳管理
│   │   │   ├── page.tsx                #   對帳總覽
│   │   │   ├── reconciliations/
│   │   │   │   ├── page.tsx            #   對帳單列表
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx        #   對帳單詳情（明細、確認）
│   │   │   ├── settlements/
│   │   │   │   └── page.tsx            #   結算記錄
│   │   │   └── vouchers/
│   │   │       └── page.tsx            #   憑證查詢
│   │   │
│   │   └── settings/                   # 系統設定
│   │       ├── page.tsx                #   設定總覽
│   │       ├── general/
│   │       │   └── page.tsx            #   一般設定（平台名稱、LINE Channel 等）
│   │       ├── ai-config/
│   │       │   └── page.tsx            #   AI 參數設定（信心閾值、模型選擇）
│   │       ├── lock-models/
│   │       │   └── page.tsx            #   電子鎖型號管理
│   │       └── users/
│   │           └── page.tsx            #   管理員帳號管理
│   │
│   └── api/                            # Next.js API Routes (BFF, 若需要)
│       └── auth/
│           └── [...nextauth]/
│               └── route.ts            #   NextAuth.js 認證端點
│
├── components/                         # ── 共用元件 ──
│   ├── ui/                             # 基礎 UI 元件（Button, Input, Modal, Table 等）
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── select.tsx
│   │   ├── modal.tsx
│   │   ├── data-table.tsx              #   通用資料表格（排序、篩選、分頁）
│   │   ├── badge.tsx
│   │   ├── card.tsx
│   │   ├── toast.tsx
│   │   └── loading-spinner.tsx
│   ├── layout/                         # 佈局元件
│   │   ├── sidebar.tsx                 #   側邊欄導航
│   │   ├── top-nav.tsx                 #   頂部導航列
│   │   ├── breadcrumb.tsx              #   麵包屑導航
│   │   └── page-header.tsx             #   頁面標題區塊
│   ├── features/                       # 業務功能元件
│   │   ├── conversation-timeline.tsx   #   對話訊息時間軸
│   │   ├── problem-card-viewer.tsx     #   問題卡結構化檢視
│   │   ├── knowledge-search.tsx        #   知識庫搜尋元件
│   │   ├── sop-review-panel.tsx        #   SOP 審核面板
│   │   ├── work-order-kanban.tsx       #   V2.0 - 工單看板
│   │   ├── technician-map.tsx          #   V2.0 - 技師地圖標記
│   │   ├── quotation-builder.tsx       #   V2.0 - 報價單建構器
│   │   └── reconciliation-table.tsx    #   V2.0 - 對帳明細表
│   └── providers/                      # Context Providers
│       ├── auth-provider.tsx           #   認證狀態管理
│       ├── theme-provider.tsx          #   主題（淺色/深色）
│       └── toast-provider.tsx          #   全域通知
│
├── lib/                                # ── 工具函式與 API 客戶端 ──
│   ├── api/                            # 後端 API 客戶端
│   │   ├── client.ts                   #   Axios/Fetch 封裝（攔截器、token 注入、錯誤處理）
│   │   ├── conversations.ts            #   對話相關 API
│   │   ├── problem-cards.ts            #   問題卡相關 API
│   │   ├── knowledge-base.ts           #   知識庫相關 API
│   │   ├── work-orders.ts              #   V2.0 - 派工相關 API
│   │   ├── technicians.ts              #   V2.0 - 技師相關 API
│   │   ├── pricing.ts                  #   V2.0 - 報價相關 API
│   │   ├── accounting.ts               #   V2.0 - 對帳相關 API
│   │   └── auth.ts                     #   認證相關 API
│   ├── hooks/                          # 自訂 React Hooks
│   │   ├── useAuth.ts                  #   認證狀態 hook
│   │   ├── usePagination.ts            #   分頁 hook
│   │   ├── useDebounce.ts              #   防抖 hook
│   │   └── useWebSocket.ts             #   V2.0 - WebSocket 即時通知
│   ├── utils/                          # 通用工具函式
│   │   ├── format.ts                   #   日期、金額格式化
│   │   ├── validation.ts               #   前端驗證規則
│   │   └── constants.ts                #   前端常數（狀態標籤、顏色對應等）
│   └── types/                          # TypeScript 型別定義
│       ├── api.ts                      #   API 請求/回應型別
│       ├── entities.ts                 #   業務實體型別
│       └── common.ts                   #   通用型別（Pagination, SortOrder 等）
│
└── __tests__/                          # 前端測試（Jest + React Testing Library）
    ├── components/
    │   ├── ui/
    │   │   └── button.test.tsx
    │   └── features/
    │       ├── problem-card-viewer.test.tsx
    │       └── work-order-kanban.test.tsx
    ├── lib/
    │   └── api/
    │       └── client.test.ts
    └── app/
        └── dashboard/
            └── page.test.tsx
```

### 5.1 src/app/ - Next.js App Router

採用 Next.js App Router 的檔案系統路由。關鍵路由群組：

| 路由群組 | 用途 | 佈局 |
|----------|------|------|
| `(auth)/` | 登入、忘記密碼 | 置中卡片，無側邊欄 |
| `(dashboard)/` | 所有後台管理頁面 | 側邊欄 + 頂部導航 |

頁面與 API 端點的對應關係：

| 前端頁面 | 後端 API |
|----------|----------|
| `/dashboard` | `GET /api/v1/dashboard/stats` |
| `/conversations` | `GET /api/v1/conversations` |
| `/problem-cards` | `GET /api/v1/problem-cards` |
| `/knowledge-base/cases` | `GET /api/v1/knowledge-base/cases` |
| `/knowledge-base/sop-drafts` | `GET /api/v1/sop-drafts` |
| `/work-orders` | `GET /api/v1/work-orders` (V2.0) |
| `/technicians` | `GET /api/v1/technicians` (V2.0) |
| `/accounting/reconciliations` | `GET /api/v1/accounting/reconciliations` (V2.0) |

### 5.2 src/components/ - 共用元件

元件分為三個層次：

- **`ui/`**：純 UI 元件，無業務邏輯。可跨專案複用。基於 shadcn/ui 或類似元件庫客製化。
- **`layout/`**：佈局結構元件，定義頁面骨架。
- **`features/`**：業務功能元件，包含特定業務邏輯，與後端 API 型別緊密耦合。

### 5.3 src/lib/ - 工具函式與 API 客戶端

- **`api/`**：每個後端領域對應一個 API 模組，封裝所有 HTTP 請求。`client.ts` 統一處理 token 注入、錯誤攔截、回應格式化。
- **`hooks/`**：封裝常用的狀態邏輯，保持元件簡潔。
- **`types/`**：TypeScript 型別定義，確保前後端型別一致。可由 `scripts/generate_api_client.sh` 從 OpenAPI spec 自動生成。

---

## 6. Docker 與部署結構

### 6.1 docker-compose.yml 服務定義

```plaintext
docker-compose.yml
│
├── backend                             # FastAPI 後端服務
│   ├── build: ./backend
│   ├── ports: 8000:8000
│   ├── depends_on: db, redis
│   ├── env_file: .env
│   └── volumes: ./backend/src:/app/src (開發環境 hot reload)
│
├── frontend                            # Next.js 前端服務（V2.0）
│   ├── build: ./frontend
│   ├── ports: 3000:3000
│   ├── depends_on: backend
│   └── env_file: .env
│
├── db                                  # PostgreSQL 16 + pgvector
│   ├── image: pgvector/pgvector:pg16
│   ├── ports: 5432:5432
│   ├── volumes: pgdata:/var/lib/postgresql/data
│   └── environment:
│       ├── POSTGRES_DB: smart_lock
│       ├── POSTGRES_USER: (from .env)
│       └── POSTGRES_PASSWORD: (from .env)
│
├── redis                               # Redis 快取
│   ├── image: redis:7-alpine
│   ├── ports: 6379:6379
│   └── volumes: redisdata:/data
│
└── nginx                               # Nginx 反向代理
    ├── image: nginx:alpine
    ├── ports: 80:80, 443:443
    ├── depends_on: backend, frontend
    └── volumes: ./nginx/conf.d:/etc/nginx/conf.d
```

**Nginx 路由規則：**

| 路徑 | 上游服務 | 說明 |
|------|---------|------|
| `/api/v1/*` | `backend:8000` | 後端 REST API |
| `/webhook/*` | `backend:8000` | LINE Webhook |
| `/docs`, `/openapi.json` | `backend:8000` | FastAPI 自動生成的 API 文件 |
| `/*` | `frontend:3000` | Next.js 前端（V2.0） |

### 6.2 .github/workflows/

```plaintext
.github/workflows/
│
├── ci.yml                              # 持續整合（每次 push / PR 觸發）
│   ├── jobs:
│   │   ├── lint-backend:               #   ruff check + mypy
│   │   ├── test-backend:               #   pytest（含 PostgreSQL service container）
│   │   ├── lint-frontend:              #   eslint + tsc --noEmit (V2.0)
│   │   └── test-frontend:              #   jest (V2.0)
│   └── triggers: push, pull_request
│
└── deploy.yml                          # 持續部署（merge 到 main 時觸發）
    ├── jobs:
    │   ├── build-images:               #   docker build + push to registry
    │   ├── run-migrations:             #   alembic upgrade head
    │   └── deploy:                     #   docker-compose up -d (或 K8s apply)
    └── triggers: push to main
```

---

## 7. 設定檔結構

### 7.1 環境變數 (.env)

`.env.example` 列出所有必要的環境變數，實際 `.env` 不納入版本控制。

```plaintext
# === Application ===
APP_ENV=development                     # development / staging / production
APP_DEBUG=true
APP_SECRET_KEY=your-secret-key-here

# === Database ===
DATABASE_URL=postgresql+asyncpg://user:password@db:5432/smart_lock
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# === Redis ===
REDIS_URL=redis://redis:6379/0
SESSION_TTL_SECONDS=3600

# === LINE Messaging API ===
LINE_CHANNEL_SECRET=your-channel-secret
LINE_CHANNEL_ACCESS_TOKEN=your-access-token

# === OpenAI ===
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# === Auth ===
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# === AI Engine ===
CASE_LIBRARY_CONFIDENCE_THRESHOLD=0.85
RAG_CONFIDENCE_THRESHOLD=0.70
VECTOR_SEARCH_TOP_K=5

# === PostgreSQL (docker-compose) ===
POSTGRES_DB=smart_lock
POSTGRES_USER=smartlock
POSTGRES_PASSWORD=your-db-password
```

### 7.2 configs/settings.toml

存放非機密的應用程式設定，可納入版本控制。

```toml
[app]
name = "Smart Lock AI Support Platform"
version = "1.0.0"
api_prefix = "/api/v1"

[conversation]
max_turns = 20
context_window_size = 10
session_timeout_minutes = 60

[problem_card]
auto_generate_threshold = 3    # 幾輪對話後自動產生問題卡
required_fields = ["lock_model", "fault_symptom"]

[resolution]
case_library_top_k = 5
rag_chunk_top_k = 8
rag_max_tokens = 1500

[content_filter]
enabled = true
max_input_length = 2000
blocked_patterns_file = "configs/blocked_patterns.txt"
```

### 7.3 configs/prompts/

LLM System Prompt 以純文字檔案儲存，方便非工程人員編輯與版本追蹤。每個 prompt 對應一個 LangChain chain。

| 檔案 | 對應 Chain | 用途 |
|------|-----------|------|
| `intent_recognition.txt` | `intent_chain.py` | 辨識用戶意圖（報修、查詢、操作指導等） |
| `ner_extraction.txt` | `ner_chain.py` | 擷取鎖型、故障症狀、錯誤代碼等實體 |
| `problem_card_gen.txt` | `problem_card_chain.py` | 從對話上下文自動生成問題卡 |
| `rag_answer.txt` | `rag_chain.py` | 基於檢索到的手冊片段生成回答 |
| `sop_draft.txt` | `sop_draft_chain.py` | 從成功案例自動撰寫 SOP 草稿 |
| `content_filter.txt` | `content_filter_chain.py` | 偵測並過濾不當內容與 prompt injection |

---

## 8. 檔案命名約定

### 8.1 Python（後端）

| 類別 | 約定 | 範例 |
|------|------|------|
| 模組/檔案 | `snake_case.py` | `problem_card_repo.py` |
| 目錄 | `snake_case` | `knowledge_base/` |
| 類別 | `PascalCase` | `ProblemCard`, `ResolveQueryUseCase` |
| 函式/方法 | `snake_case` | `create_problem_card()` |
| 常數 | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT` |
| 測試檔案 | `test_*.py` | `test_resolve_query.py` |
| Pydantic DTO | `PascalCase` + 後綴 `DTO` | `ProblemCardCreateDTO` |
| Protocol | `PascalCase` + 後綴 `Repository`/`Service` | `CaseRepository`, `LLMService` |

### 8.2 TypeScript / React（前端）

| 類別 | 約定 | 範例 |
|------|------|------|
| React 元件 | `PascalCase.tsx` | `ProblemCardViewer.tsx` |
| 工具函式/Hook | `camelCase.ts` | `useDebounce.ts`, `format.ts` |
| 目錄 | `kebab-case` | `knowledge-base/`, `work-orders/` |
| API 模組 | `kebab-case.ts` | `problem-cards.ts` |
| 型別定義 | `camelCase.ts` | `entities.ts` |
| 測試檔案 | `*.test.ts` / `*.test.tsx` | `button.test.tsx` |
| CSS 模組 | `camelCase.module.css` | `sidebar.module.css` |
| Next.js 頁面 | `page.tsx`（固定） | `app/dashboard/page.tsx` |

### 8.3 其他檔案

| 類別 | 約定 | 範例 |
|------|------|------|
| Markdown 文件 | `snake_case.md` 或編號前綴 | `08_project_structure_guide.md` |
| Shell 腳本 | `snake_case.sh` | `setup_dev.sh` |
| Docker 設定 | 官方慣例 | `Dockerfile`, `docker-compose.yml` |
| 環境變數 | `UPPER_SNAKE_CASE` | `DATABASE_URL` |
| Alembic 遷移 | 編號前綴 + 描述 | `004_add_pgvector_extension.py` |

---

## 9. 演進原則

### 9.1 版本演進路線

```plaintext
V1.0 (LINE Bot + Admin API)              V2.0 (+ 技師工作台 + 派工/報價/對帳)
================================          ====================================

smart-lock-platform/                      smart-lock-platform/
├── backend/                              ├── backend/
│   └── src/smart_lock/                   │   └── src/smart_lock/
│       ├── domains/                      │       ├── domains/
│       │   ├── conversation/             │       │   ├── conversation/
│       │   ├── problem_card/             │       │   ├── problem_card/
│       │   ├── knowledge_base/           │       │   ├── knowledge_base/
│       │   └── resolution/               │       │   ├── resolution/
│       ├── application/                  │       │   ├── dispatch/        [NEW]
│       │   ├── conversation/             │       │   ├── pricing/         [NEW]
│       │   ├── problem_card/             │       │   └── accounting/      [NEW]
│       │   ├── knowledge_base/           │       ├── application/
│       │   └── resolution/               │       │   ├── ...existing...
│       └── infrastructure/               │       │   ├── dispatch/        [NEW]
│           ├── web/routers/              │       │   ├── pricing/         [NEW]
│           ├── persistence/              │       │   └── accounting/      [NEW]
│           ├── external/                 │       └── infrastructure/
│           └── cache/                    │           ├── web/routers/
├── configs/                              │           │   ├── ...existing...
├── data/                                 │           │   ├── work_orders.py    [NEW]
├── scripts/                              │           │   ├── technicians.py    [NEW]
├── docs/                                 │           │   ├── quotations.py     [NEW]
└── docker-compose.yml                    │           │   └── accounting.py     [NEW]
                                          │           └── ...existing...
   (無 frontend/ 目錄)                    ├── frontend/                    [NEW]
                                          │   └── src/
                                          │       ├── app/
                                          │       ├── components/
                                          │       └── lib/
                                          └── docker-compose.yml (新增 frontend service)
```

### 9.2 新增模組的標準流程

當需要新增一個業務模組（例如「通知中心」）時，遵循以下步驟：

1. **建立 Domain 層：** `backend/src/smart_lock/domains/notification/`
   - `entities.py` - 定義核心實體
   - `value_objects.py` - 定義值物件

2. **建立 Application 層：** `backend/src/smart_lock/application/notification/`
   - `use_cases.py` - 定義業務用例
   - `dtos.py` - 定義資料傳輸物件
   - `interfaces.py` - 定義 Repository Protocol

3. **建立 Infrastructure 層：**
   - `infrastructure/web/routers/notifications.py` - API 端點
   - `infrastructure/persistence/orm_models/notification_model.py` - ORM 模型
   - `infrastructure/persistence/repositories/notification_repo.py` - Repository 實作

4. **建立測試：**
   - `tests/unit/domains/test_notification_entities.py`
   - `tests/unit/application/test_notification_use_cases.py`
   - `tests/features/test_notification_api.py`

5. **建立遷移：** `alembic/versions/xxx_create_notifications.py`

6. **註冊路由：** 在 `main.py` 中 `include_router()`

### 9.3 結構變更原則

- 任何**頂層目錄結構**的變更，必須透過 ADR（Architecture Decision Record）記錄。
- 新增領域模組遵循上述標準流程，無需 ADR。
- `core/` 中新增共用模組需經過 code review 確認其確實為跨領域共用。
- 保持**可預測性**比追求「完美結構」更重要 --- 一致性是第一優先。

---

## 附錄 A：快速定位指南

| 我想找... | 去哪裡看 |
|----------|---------|
| LINE Webhook 處理邏輯 | `backend/src/smart_lock/infrastructure/web/routers/webhook.py` |
| 問題卡的業務規則 | `backend/src/smart_lock/domains/problem_card/entities.py` |
| 三層解析引擎的流程 | `backend/src/smart_lock/application/resolution/use_cases.py` |
| RAG chain 的 prompt | `configs/prompts/rag_answer.txt` |
| LangChain chain 定義 | `backend/src/smart_lock/infrastructure/external/langchain_chains/` |
| 資料庫 schema | `backend/src/smart_lock/infrastructure/persistence/orm_models/` |
| 向量搜尋實作 | `backend/src/smart_lock/infrastructure/persistence/repositories/case_repo.py` |
| 對話 session 快取 | `backend/src/smart_lock/infrastructure/cache/session_store.py` |
| API 端點列表 | FastAPI 自動生成：`http://localhost:8000/docs` |
| 前端頁面路由 | `frontend/src/app/` 目錄結構即路由結構 |
| 環境變數說明 | `.env.example` |
| LLM prompt 模板 | `configs/prompts/` |
| 資料庫遷移歷史 | `backend/alembic/versions/` |
| CI/CD 流程 | `.github/workflows/` |
| 架構決策記錄 | `docs/adrs/` |

## 附錄 B：依賴方向圖

```plaintext
                    ┌─────────────────────┐
                    │   main.py (入口)     │
                    └──────────┬──────────┘
                               │ 組裝所有元件
                               ▼
┌──────────────────────────────────────────────────────┐
│                 Infrastructure Layer                  │
│                                                      │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌───────┐ │
│  │ Routers │  │ Repos    │  │External │  │ Cache │ │
│  │(FastAPI)│  │(SQLAlchm)│  │(LINE,   │  │(Redis)│ │
│  │         │  │          │  │ OpenAI, │  │       │ │
│  │         │  │          │  │ LangChn)│  │       │ │
│  └────┬────┘  └────┬─────┘  └────┬────┘  └───┬───┘ │
│       │            │             │            │      │
└───────┼────────────┼─────────────┼────────────┼──────┘
        │            │             │            │
        ▼            ▼             ▼            ▼
┌──────────────────────────────────────────────────────┐
│                  Application Layer                    │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │  Use Cases   │  │    DTOs      │  │ Interfaces│  │
│  │  (編排業務   │  │ (資料傳輸    │  │ (Protocol │  │
│  │   流程)      │  │  物件)       │  │  定義)    │  │
│  └──────┬───────┘  └──────────────┘  └───────────┘  │
│         │                                            │
└─────────┼────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────┐
│                    Domain Layer                       │
│                                                      │
│  ┌──────────┐  ┌───────────────┐  ┌──────────────┐  │
│  │ Entities │  │ Value Objects │  │Domain Events │  │
│  │ (業務    │  │ (值物件)      │  │ (領域事件)   │  │
│  │  實體)   │  │               │  │              │  │
│  └──────────┘  └───────────────┘  └──────────────┘  │
│                                                      │
│               零外部依賴，純業務邏輯                   │
└──────────────────────────────────────────────────────┘
```

**依賴規則：** 箭頭方向代表依賴方向。外層可以依賴內層，內層絕不依賴外層。Infrastructure 透過 Application 層定義的 Protocol (interfaces.py) 實作依賴反轉。
