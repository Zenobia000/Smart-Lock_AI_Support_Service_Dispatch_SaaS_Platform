# 系統架構總覽 - 電子鎖智能客服與派工平台

---

## 1. 系統分層堆疊圖

由上至下六層，上層依賴下層，每層標註具體技術選型。

```mermaid
graph TB
    L1["<b>使用者介面層</b><br/>LINE Messaging API | Next.js 14 + React 19 | shadcn/ui + Tailwind | PWA"]
    L2["<b>API 閘道層</b><br/>FastAPI + Uvicorn | Pydantic v2 | OpenAPI/Swagger | JWT + RBAC"]
    L3["<b>AI 服務層</b><br/>LangChain 0.3 LCEL | Google Gemini 3 Pro | text-embedding-004 768d | LangSmith"]
    L4["<b>業務領域層</b><br/>customer_service | knowledge_base | dispatch V2.0 | accounting V2.0"]
    L5["<b>資料存取層</b><br/>SQLAlchemy 2.0 Async | asyncpg | Alembic Migration | Redis aioredis"]
    L6["<b>基礎設施層</b><br/>PostgreSQL 16 + pgvector 0.7 | Redis 7 | Docker Compose | TLS 1.2+ / AES-256"]

    L1 --> L2
    L2 --> L3
    L2 --> L4
    L3 --> L4
    L4 --> L5
    L5 --> L6

    classDef s1 fill:#E3F2FD,stroke:#1565C0,stroke-width:2px
    classDef s2 fill:#FFF3E0,stroke:#E65100,stroke-width:2px
    classDef s3 fill:#EDE7F6,stroke:#4527A0,stroke-width:2px
    classDef s4 fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px
    classDef s5 fill:#F3E5F5,stroke:#6A1B9A,stroke-width:2px
    classDef s6 fill:#ECEFF1,stroke:#37474F,stroke-width:2px
    class L1 s1
    class L2 s2
    class L3 s3
    class L4 s4
    class L5 s5
    class L6 s6
```

---

## 2. 系統架構圖 - 資訊流

從消費者發起問題到結案的完整資訊流動路徑，涵蓋三類使用者、平台核心與外部系統。

```mermaid
graph TD
    subgraph 使用者
        C[fa:fa-user 消費者 - LINE]
        T[fa:fa-wrench 技師 - Web App]
        A[fa:fa-user 管理員 - Admin Panel]
    end

    subgraph 平台核心
        subgraph 介面層
            BOT[fa:fa-comments LINE Bot AI 客服]
            WEB[fa:fa-mobile 技師工作台]
            ADM[fa:fa-bar-chart 營運儀表板]
        end

        subgraph AI 引擎
            PC[fa:fa-stethoscope 問題診斷引擎]
            RES[fa:fa-lightbulb-o 三層解決引擎]
            SOP[fa:fa-file-text SOP 自動生成]
        end

        subgraph 業務引擎
            DSP[fa:fa-cogs 智慧派工引擎]
            PRC[fa:fa-tags 報價引擎]
            ACC[fa:fa-money 帳務模組]
        end

        subgraph 資料層
            DB[fa:fa-database PostgreSQL]
            VEC[fa:fa-book pgvector 知識庫]
            RED[fa:fa-bolt Redis 快取]
        end
    end

    subgraph 外部服務
        LINE_API[fa:fa-commenting LINE API]
        GEMINI[fa:fa-cloud Google Gemini AI]
    end

    C -->|1. 報修諮詢| BOT
    BOT -->|2. 收發訊息| LINE_API
    LINE_API -->|3. Webhook| PC

    PC -->|4. 產生問題卡| RES
    RES -->|5a. L1 查知識庫| VEC
    RES -->|5b. L2 AI 推理| GEMINI
    RES -->|6. 回覆方案| BOT
    RES -->|7. L3 轉派工| DSP

    DSP -->|8. 查詢報價| PRC
    DSP -->|9. 派單通知| WEB
    T -->|10. 接單回報| WEB
    WEB -->|11. 更新工單| DSP
    DSP -->|12. 結案| ACC

    RES -.->|成功案例| SOP
    SOP -.->|審核後入庫| VEC

    A -->|監控管理| ADM
    ADM --> DSP
    ADM --> VEC

    PC --> DB
    DSP --> DB
    ACC --> DB
    RES --> RED

    classDef userStyle fill:#E3F2FD,stroke:#1565C0,stroke-width:2px
    classDef aiStyle fill:#EDE7F6,stroke:#4527A0,stroke-width:2px
    classDef bizStyle fill:#FFF3E0,stroke:#E65100,stroke-width:2px
    classDef dataStyle fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px
    classDef extStyle fill:#ECEFF1,stroke:#37474F,stroke-width:2px
    class C,T,A,BOT,WEB,ADM userStyle
    class PC,RES,SOP aiStyle
    class DSP,PRC,ACC bizStyle
    class DB,VEC,RED dataStyle
    class LINE_API,GEMINI extStyle
```

---

## 3. 功能模組清單與服務列表

### V1.0 - AI 智能客服系統

| 模組 | 服務 | 職責 | 關鍵技術 |
| :--- | :--- | :--- | :--- |
| **LINE Bot 接入** | Webhook Handler | 接收 LINE Webhook、驗證簽章、路由事件 | FastAPI, line-bot-sdk-python 3 |
| **對話管理** | ConversationService | 對話狀態機 (Idle→Collecting→Resolving→Resolved)、多輪上下文、Session 超時 30min | Redis, 狀態機模式 |
| **問題診斷** | ProblemCardService | 從自然語言提取結構化問題卡 (品牌/型號/症狀/位置)、AI 輔助欄位推斷、缺失欄位追問 | LangChain, Gemini 3 Pro |
| **三層解決引擎** | ResolutionService | L1: pgvector 語意搜尋 (相似度≥0.85) → L2: RAG + Gemini 推理 → L3: 轉人工/建工單 | LangChain LCEL, pgvector HNSW |
| **知識庫管理** | KnowledgeBaseService | 案例 CRUD、PDF 手冊上傳→分段→Embedding、向量搜尋、增量更新 | PyMuPDF, text-embedding-004 |
| **SOP 自動生成** | SOPGeneratorService | 監聽成功解決事件→分析對話→AI 草擬 SOP→提交審核佇列 | LangChain, 事件驅動 |
| **LLM 閘道** | LLMGateway | 統一 LLM 呼叫入口、Prompt 模板管理、Token 追蹤、Retry/Fallback | LangChain, Google AI SDK |
| **管理後台** | Admin Panel | 知識庫審核、對話紀錄查詢、系統監控、SOP 上架管理 | FastAPI + Jinja2/HTMX (V1.0) |

### V2.0 - 派工與帳務系統

| 模組 | 服務 | 職責 | 關鍵技術 |
| :--- | :--- | :--- | :--- |
| **智慧派工** | DispatchService | 技師匹配 (技能×地區×評分×可用時段)、工單生命週期 (Created→Assigned→InProgress→Completed)、推播通知 | 匹配演算法, WebSocket |
| **報價引擎** | PricingService | 計價規則 (品牌×鎖型×難度)、自動報價生成、客戶確認流程 | 規則引擎模式 |
| **帳務結算** | AccountingService | 對帳作業、發票/請款單生成、技師佣金計算、統計報表 | PostgreSQL 交易 |
| **技師工作台** | Technician Web App | 可接案件列表、一鍵接單、進度回報、導航整合、個人帳務 | Next.js 14 + PWA |
| **增強管理後台** | Enhanced Admin Panel | 派工監控、技師管理、帳務審核、營運儀表板 | Next.js 14 + shadcn/ui |

### 跨模組共用服務

| 服務 | 職責 |
| :--- | :--- |
| **UserManagement** | LINE 用戶綁定、技師/管理員帳號、JWT 認證、RBAC 權限 (admin/technician/user) |
| **NotificationService** | LINE Push Message、Web Push (技師端)、系統內通知 |
| **ObservabilityStack** | 結構化日誌 (JSON)、LangSmith LLM 追蹤、Health Check API |

---
