# 整合性架構與設計文件 - 電子鎖智能客服與派工平台

# Smart Lock AI Support & Service Dispatch SaaS Platform

---

**文件版本 (Document Version):** `v1.0`
**最後更新 (Last Updated):** `2026-02-17`
**主要作者 (Lead Author):** `技術架構師`
**審核者 (Reviewers):** `架構委員會, 核心開發團隊`
**狀態 (Status):** `已批准 (Approved)`

---

## 目錄 (Table of Contents)

- [第 1 部分：架構總覽](#第-1-部分架構總覽)
  - [1.1 C4 模型：視覺化架構](#11-c4-模型視覺化架構)
  - [1.2 DDD 戰略設計](#12-ddd-戰略設計)
  - [1.3 Clean Architecture 分層](#13-clean-architecture-分層)
  - [1.4 技術選型與決策](#14-技術選型與決策)
- [第 2 部分：需求摘要](#第-2-部分需求摘要)
  - [2.1 功能性需求摘要](#21-功能性需求摘要)
  - [2.2 非功能性需求](#22-非功能性需求)
- [第 3 部分：高層次架構設計](#第-3-部分高層次架構設計)
  - [3.1 架構模式](#31-架構模式)
  - [3.2 系統上下文圖](#32-系統上下文圖)
  - [3.3 系統組件圖](#33-系統組件圖)
  - [3.4 主要組件職責表](#34-主要組件職責表)
  - [3.5 關鍵用戶旅程](#35-關鍵用戶旅程)
- [第 4 部分：技術選型詳述](#第-4-部分技術選型詳述)
- [第 5 部分：數據架構](#第-5-部分數據架構)
  - [5.1 數據模型](#51-數據模型)
  - [5.2 數據流圖](#52-數據流圖)
  - [5.3 數據一致性策略](#53-數據一致性策略)
  - [5.4 向量索引策略](#54-向量索引策略)
- [第 6 部分：部署與基礎設施](#第-6-部分部署與基礎設施)
  - [6.1 部署視圖](#61-部署視圖)
  - [6.2 CI/CD 流程](#62-cicd-流程)
  - [6.3 環境策略](#63-環境策略)
- [第 7 部分：跨領域考量](#第-7-部分跨領域考量)
  - [7.1 可觀測性](#71-可觀測性)
  - [7.2 安全性](#72-安全性)
- [第 8 部分：風險與緩解策略](#第-8-部分風險與緩解策略)
- [第 9 部分：架構演進路線圖](#第-9-部分架構演進路線圖)
- [第 10 部分：附錄](#第-10-部分附錄)

---

**目的**: 本文件旨在將電子鎖智能客服與派工平台的業務需求轉化為一個完整、內聚的技術藍圖。系統分為兩個主要階段交付：V1.0 聚焦 AI 智能客服（LINE Bot + AI 問診 + ProblemCard + 三層解決機制 + 自演化知識庫 + 管理後台），V2.0 擴展至技師派工與帳務（技師工作台 Web App + 智能派工 + 計價引擎 + 帳務系統 + 增強管理後台）。本文件從高層次的系統架構出發，逐步深入到具體的模組級設計，確保系統的穩固性與可維護性。

---

## 第 1 部分：架構總覽

*此部分關注系統的宏觀結構與指導原則，回答「系統由什麼組成？」以及「它們之間如何互動？」。*

### 1.1 C4 模型：視覺化架構

我們使用 [C4 模型](https://c4model.com/) 從不同層次視覺化軟體架構，確保從利害關係人到開發者的每個角色都能清楚理解系統結構。

#### L1 - 系統情境圖 (System Context Diagram)

描述本系統與外部使用者及外部系統的互動邊界。本平台服務三類使用者：一般用戶（透過 LINE）、技師（透過 Web App）、管理員（透過管理後台），並與 LINE Messaging API 和 OpenAI API 兩個外部系統整合。

```mermaid
graph TB
    subgraph "外部使用者 (External Users)"
        LU["LINE 用戶<br/>(一般消費者 / 住戶)<br/>---<br/>透過 LINE App 發起<br/>電子鎖問題諮詢"]
        TU["技師<br/>(Technician)<br/>---<br/>V2.0 透過 Web App<br/>接收與處理派工單"]
        AU["管理員<br/>(Admin / 客服主管)<br/>---<br/>透過管理後台<br/>監控系統與管理知識庫"]
    end

    subgraph "Smart Lock AI Support Platform"
        SYS["電子鎖智能客服與派工平台<br/>(Smart Lock AI Platform)<br/>---<br/>提供 AI 問診、三層解決機制<br/>知識庫管理、派工調度、帳務處理"]
    end

    subgraph "外部系統 (External Systems)"
        LINE["LINE Messaging API<br/>---<br/>訊息收發、Rich Menu<br/>Flex Message 推送"]
        OPENAI["OpenAI GPT-4o API<br/>---<br/>自然語言理解、意圖識別<br/>對話生成、SOP 草稿生成"]
    end

    LU -- "LINE 訊息<br/>(文字/圖片/位置)" --> SYS
    SYS -- "回覆訊息<br/>(Flex Message / 文字)" --> LU
    TU -- "HTTPS<br/>(REST API)" --> SYS
    SYS -- "派工通知<br/>(Push Notification)" --> TU
    AU -- "HTTPS<br/>(Web Admin Panel)" --> SYS
    SYS -- "Webhook Events" --> LINE
    LINE -- "Webhook Callback" --> SYS
    SYS -- "LLM API Calls<br/>(Chat Completion)" --> OPENAI
    OPENAI -- "AI Response<br/>(JSON)" --> SYS
```

#### L2 - 容器圖 (Container Diagram)

描述系統由哪些可部署單元組成。V1.0 階段以 FastAPI 後端為核心，搭配 PostgreSQL + pgvector 與 Redis。V2.0 增加 Next.js 前端。

```mermaid
graph TB
    subgraph "外部使用者"
        LU["LINE 用戶"]
        TU["技師 (V2.0)"]
        AU["管理員"]
    end

    subgraph "外部系統"
        LINE_API["LINE Messaging API"]
        OPENAI_API["OpenAI GPT-4o API"]
    end

    subgraph "Platform Containers"
        subgraph "Web 層 (Web Tier)"
            WEBHOOK["LINE Bot Webhook Handler<br/>---<br/>Python / FastAPI<br/>接收 LINE Webhook 事件<br/>驗證簽章、路由事件"]
            ADMIN["Admin Panel<br/>---<br/>V1.0: FastAPI + Jinja2 / HTMX<br/>V2.0: Next.js (React/TypeScript)<br/>知識庫管理、系統監控"]
            TECHAPP["Technician Web App<br/>---<br/>V2.0: Next.js (React/TypeScript)<br/>派工接收、工單回報、導航"]
        end

        subgraph "API 層 (API Tier)"
            API["FastAPI Backend<br/>(Core Application Server)<br/>---<br/>Python 3.11+ / FastAPI / Uvicorn<br/>REST API / WebSocket<br/>業務邏輯核心"]
        end

        subgraph "數據層 (Data Tier)"
            PG["PostgreSQL 16<br/>+ pgvector Extension<br/>---<br/>主要關聯式資料庫<br/>向量索引 (HNSW)<br/>案例庫 & 手冊嵌入"]
            REDIS["Redis<br/>---<br/>Session Cache<br/>對話狀態暫存<br/>Rate Limiting Counter"]
        end
    end

    LU -- "LINE Messages" --> LINE_API
    LINE_API -- "Webhook POST<br/>(HTTPS + Signature)" --> WEBHOOK
    WEBHOOK -- "Internal Route" --> API
    API -- "Reply/Push API<br/>(HTTPS)" --> LINE_API

    TU -- "HTTPS<br/>(REST API)" --> TECHAPP
    TECHAPP -- "API Calls<br/>(HTTPS)" --> API

    AU -- "HTTPS<br/>(Browser)" --> ADMIN
    ADMIN -- "API Calls<br/>(HTTPS)" --> API

    API -- "LangChain<br/>(Chat Completion / Embedding)" --> OPENAI_API
    API -- "SQL / pgvector<br/>(SQLAlchemy Async)" --> PG
    API -- "Cache R/W<br/>(aioredis)" --> REDIS
```

#### L3 - 元件圖 (Component Diagram) - FastAPI Backend 內部

針對核心容器 FastAPI Backend，拆解其內部的模組元件。這是系統的業務邏輯核心。

```mermaid
graph TB
    subgraph "FastAPI Backend - Internal Components"

        subgraph "Interface Layer (介面層)"
            WH["Webhook Controller<br/>---<br/>LINE 事件接收與路由<br/>簽章驗證"]
            REST["REST API Controllers<br/>---<br/>Admin API / Technician API<br/>Knowledge Base API"]
        end

        subgraph "Application Layer (應用層)"
            CM["Conversation Manager<br/>---<br/>對話狀態機管理<br/>Session 生命週期<br/>多輪對話上下文維護"]
            PCE["ProblemCard Engine<br/>---<br/>問題卡建立與填充<br/>欄位驗證與完整性檢查<br/>AI 輔助欄位推斷"]
            TLR["Three-Layer Resolver<br/>---<br/>L1: 知識庫精確匹配<br/>L2: AI 推理生成<br/>L3: 轉人工 / 建立工單"]
            KBM["Knowledge Base Manager<br/>---<br/>案例庫 CRUD<br/>手冊 PDF 解析與分段<br/>Embedding 生成與更新"]
            SOPGen["SOP Generator<br/>---<br/>從成功對話中<br/>自動草擬 SOP<br/>待人工審核後上架"]
        end

        subgraph "Application Layer V2.0 (派工與帳務)"
            DSP["Dispatch Engine<br/>---<br/>智能技師匹配<br/>技能 / 地區 / 評分<br/>工單生命週期管理"]
            PRC["Pricing Engine<br/>---<br/>品牌 x 鎖型 x 難度<br/>計價規則引擎<br/>報價生成"]
            ACC["Accounting Module<br/>---<br/>對帳作業<br/>發票 / 請款單<br/>統計報表"]
        end

        subgraph "Domain Layer (領域層)"
            ENT["Domain Entities<br/>---<br/>ProblemCard / Conversation<br/>CaseEntry / ManualChunk<br/>WorkOrder / Technician<br/>PriceRule / Invoice"]
            EVT["Domain Events<br/>---<br/>CardCompleted<br/>ResolutionFound<br/>WorkOrderCreated<br/>WorkOrderCompleted"]
        end

        subgraph "Infrastructure Layer (基礎設施層)"
            REPO["Repositories<br/>---<br/>SQLAlchemy Async Repos<br/>pgvector Search Repos<br/>Redis Cache Repos"]
            LLM["LLM Gateway<br/>---<br/>LangChain Wrapper<br/>OpenAI API Client<br/>Prompt Template Manager<br/>Token Usage Tracker"]
            LINEsdk["LINE SDK Adapter<br/>---<br/>line-bot-sdk-python<br/>Message Builder<br/>Flex Message Templates"]
            EMB["Embedding Service<br/>---<br/>text-embedding-3-small<br/>Batch Embedding Pipeline<br/>Vector Normalization"]
        end
    end

    WH --> CM
    WH --> PCE
    REST --> KBM
    REST --> DSP
    REST --> ACC

    CM --> TLR
    CM --> PCE
    PCE --> TLR
    TLR --> KBM
    TLR --> SOPGen
    TLR --> DSP

    CM --> ENT
    PCE --> ENT
    TLR --> ENT
    KBM --> ENT
    DSP --> ENT
    PRC --> ENT
    ACC --> ENT

    CM --> EVT
    PCE --> EVT
    TLR --> EVT
    DSP --> EVT

    ENT --> REPO
    KBM --> EMB
    TLR --> LLM
    SOPGen --> LLM
    PCE --> LLM
    CM --> LINEsdk
    CM --> REPO
    DSP --> REPO
    PRC --> REPO
    ACC --> REPO

    LINEsdk --> LINEEXT["LINE Messaging API"]
    LLM --> OAIEXT["OpenAI API"]
    REPO --> PGEXT["PostgreSQL + pgvector"]
    REPO --> RDEXT["Redis"]
```

### 1.2 DDD 戰略設計 (Strategic DDD)

#### 通用語言 (Ubiquitous Language)

以下術語在專案所有利害關係人之間共享，具有唯一且無歧義的定義：

| 術語 (Term) | 中文名稱 | 定義 (Definition) |
| :--- | :--- | :--- |
| **ProblemCard** | 問題卡 | 一次客服對話的結構化問題描述，包含電子鎖型號 (model)、安裝位置 (location)、門的狀態 (door_status)、網路狀態 (network)、故障症狀 (symptoms)、用戶意圖 (intent)、處理狀態 (status)。是三層解決機制的輸入核心。 |
| **Conversation** | 對話 | 用戶與系統之間的一次完整互動 session，由多輪訊息 (messages) 組成，關聯到一張 ProblemCard。 |
| **CaseEntry** | 案例條目 | 知識庫中的一筆案例記錄，包含問題描述、解決方案、適用品牌/型號，以及用於向量搜尋的 embedding。 |
| **ManualChunk** | 手冊段落 | 電子鎖 PDF 操作手冊經解析後的文本段落，包含 embedding，用於 RAG 檢索。 |
| **SOPDraft** | SOP 草稿 | 系統從成功對話中自動產生的標準作業程序草稿，需經管理員審核後才能加入知識庫。 |
| **Three-Layer Resolution** | 三層解決機制 | 問題解決的核心流程：L1 知識庫精確匹配 -> L2 AI 推理生成 -> L3 轉人工/建立派工單。 |
| **WorkOrder** | 派工單 | V2.0 - 由系統建立的到場服務工單，包含問題描述、客戶資訊、指派技師、預約時段、服務狀態。 |
| **Technician** | 技師 | V2.0 - 已登錄的維修技師，包含技能清單 (capabilities)、服務地區 (regions)、可用時段 (availability)、評分 (rating)。 |
| **PriceRule** | 計價規則 | V2.0 - 定義服務費用的規則，以品牌 (brand) x 鎖型 (lock_type) x 難度 (difficulty) 為維度。 |
| **Invoice** | 發票/請款單 | V2.0 - 服務完成後產生的帳務憑證，包含服務明細、金額、付款狀態。 |
| **Knowledge Base** | 知識庫 | 由 CaseEntry 和 ManualChunk 組成的可搜尋資料集合，支援向量相似度搜尋，是 L1 解決機制的資料來源。 |
| **Embedding** | 向量嵌入 | 文本經 LLM embedding model 轉換後的高維向量表示，用於語義相似度搜尋。 |
| **Rich Menu** | LINE 選單 | LINE Bot 底部的自訂選單介面，提供快捷操作入口。 |
| **Flex Message** | 彈性訊息 | LINE 的結構化訊息格式，用於呈現 ProblemCard 摘要、解決方案步驟等。 |

#### 限界上下文 (Bounded Contexts)

根據業務領域劃分的五個限界上下文：

| 限界上下文 | 英文名稱 | 核心職責 | 核心實體 | 階段 |
| :--- | :--- | :--- | :--- | :--- |
| **客服上下文** | CustomerService | LINE Bot 互動、對話管理、ProblemCard 建立與填充、三層解決機制執行 | Conversation, ProblemCard, Message | V1.0 |
| **知識庫上下文** | KnowledgeBase | 案例管理、手冊解析、Embedding 計算、向量搜尋、SOP 自動生成與審核 | CaseEntry, ManualChunk, SOPDraft, Embedding | V1.0 |
| **派工上下文** | Dispatch | 工單建立與管理、技師匹配與指派、排程、工單狀態追蹤 | WorkOrder, Technician, Assignment | V2.0 |
| **帳務上下文** | Accounting | 計價規則管理、報價生成、對帳、發票管理、統計報表 | PriceRule, Invoice, Voucher, Report | V2.0 |
| **使用者管理上下文** | UserManagement | LINE 用戶綁定、管理員帳號管理、技師帳號管理、角色與權限控制 | User, Admin, Role, Permission | V1.0 + V2.0 |

#### 上下文地圖 (Context Map)

定義限界上下文之間的關係。箭頭表示依賴方向（上游 -> 下游）。

```mermaid
graph LR
    subgraph "V1.0 Core"
        CS["CustomerService<br/>(客服上下文)<br/>---<br/>核心上游"]
        KB["KnowledgeBase<br/>(知識庫上下文)<br/>---<br/>共享核心"]
        UM["UserManagement<br/>(使用者管理上下文)<br/>---<br/>通用子域"]
    end

    subgraph "V2.0 Extension"
        DP["Dispatch<br/>(派工上下文)<br/>---<br/>V2.0 核心"]
        AC["Accounting<br/>(帳務上下文)<br/>---<br/>V2.0 支援"]
    end

    CS -- "Conformist<br/>(查詢案例/手冊)" --> KB
    CS -- "Customer-Supplier<br/>(L3 建立工單)" --> DP
    CS -- "Conformist<br/>(用戶身分驗證)" --> UM

    DP -- "Customer-Supplier<br/>(服務完成 -> 產生帳務)" --> AC
    DP -- "Conformist<br/>(技師身分驗證)" --> UM
    DP -- "Anti-Corruption Layer<br/>(查詢問題卡資訊)" --> CS

    KB -- "Published Language<br/>(SOP/案例結構)" --> CS
    AC -- "Conformist<br/>(查詢工單明細)" --> DP
```

**上下文關係說明：**

| 關係 | 模式 | 說明 |
| :--- | :--- | :--- |
| CustomerService -> KnowledgeBase | Conformist | 客服上下文遵循知識庫上下文定義的資料結構進行案例查詢 |
| CustomerService -> Dispatch | Customer-Supplier | 客服上下文作為需求方，當 L3 觸發時向派工上下文提交工單建立請求 |
| KnowledgeBase -> CustomerService | Published Language | 知識庫透過公開的 CaseEntry/ManualChunk 結構提供搜尋結果 |
| Dispatch -> Accounting | Customer-Supplier | 派工完成後，派工上下文觸發帳務上下文進行費用計算與請款 |
| Dispatch -> CustomerService | Anti-Corruption Layer | 派工上下文透過防腐層轉譯客服上下文的 ProblemCard，避免領域模型耦合 |
| 所有上下文 -> UserManagement | Conformist | 所有上下文遵循 UserManagement 定義的身分與權限模型 |

### 1.3 Clean Architecture 分層

系統遵循 Clean Architecture 原則，確保關注點分離。依賴方向嚴格由外而內：Infrastructure -> Application -> Domain。

```mermaid
graph TB
    subgraph "Clean Architecture Layers"
        subgraph "Infrastructure Layer (基礎設施層) - 最外層"
            CTRL["Web Controllers<br/>LINE Webhook Handler<br/>REST API Routes"]
            REPOIMPL["Repository Implementations<br/>SQLAlchemy Models & Repos<br/>pgvector Search Implementation"]
            EXTAPI["External API Clients<br/>LangChain/OpenAI Client<br/>LINE SDK Adapter"]
            CACHE["Cache Implementation<br/>Redis Client"]
        end

        subgraph "Application Layer (應用層) - 中間層"
            UC["Use Cases / Application Services<br/>ConversationService<br/>ProblemCardService<br/>ResolutionService<br/>KnowledgeBaseService<br/>DispatchService (V2.0)<br/>PricingService (V2.0)"]
            DTO["DTOs / Request-Response Models<br/>Pydantic Schemas<br/>API Models"]
            IFACE["Port Interfaces (Abstractions)<br/>IConversationRepository<br/>ICaseEntryRepository<br/>ILLMGateway<br/>ILineMessenger"]
        end

        subgraph "Domain Layer (領域層) - 最內層"
            ENTITIES["Entities & Aggregates<br/>ProblemCard (Aggregate Root)<br/>Conversation (Aggregate Root)<br/>WorkOrder (Aggregate Root, V2.0)<br/>CaseEntry, ManualChunk<br/>Technician, PriceRule"]
            VO["Value Objects<br/>LockModel, Location<br/>DoorStatus, NetworkStatus<br/>Symptom, ResolutionLevel<br/>WorkOrderStatus"]
            DE["Domain Events<br/>ProblemCardCompleted<br/>ResolutionFound<br/>EscalatedToHuman<br/>WorkOrderAssigned (V2.0)<br/>ServiceCompleted (V2.0)"]
            DS["Domain Services<br/>ThreeLayerResolutionPolicy<br/>TechnicianMatchingPolicy (V2.0)<br/>PriceCalculationPolicy (V2.0)"]
        end
    end

    CTRL --> UC
    REPOIMPL -.->|implements| IFACE
    EXTAPI -.->|implements| IFACE
    CACHE -.->|implements| IFACE
    UC --> IFACE
    UC --> DTO
    UC --> ENTITIES
    UC --> DE
    ENTITIES --> VO
    DS --> ENTITIES
    DS --> VO
```

**各層職責明確定義：**

| 層 (Layer) | 職責 | 包含元素 | 依賴規則 |
| :--- | :--- | :--- | :--- |
| **Domain Layer** | 核心業務規則與邏輯，完全不依賴任何外部框架 | Entities, Value Objects, Domain Events, Domain Services | 不依賴任何其他層 |
| **Application Layer** | 編排業務用例流程，定義 Port 抽象介面 | Use Cases, DTOs, Port Interfaces | 僅依賴 Domain Layer |
| **Infrastructure Layer** | 實現所有外部整合的具體細節 | Controllers, Repository Impls, API Clients, Cache | 依賴 Application Layer（實現 Port Interfaces） |

### 1.4 技術選型與決策

#### 技術棧總覽 (Tech Stack Overview)

| 分類 | 選用技術 | 版本 | 用途 |
| :--- | :--- | :--- | :--- |
| **後端語言** | Python | 3.11+ | 核心業務邏輯 |
| **後端框架** | FastAPI | 0.110+ | REST API / WebSocket / Webhook |
| **ASGI Server** | Uvicorn | 0.29+ | 高效能非同步 HTTP Server |
| **LLM 框架** | LangChain | 0.2+ | LLM 調用抽象、Chain 編排、Prompt 管理 |
| **LLM 模型** | OpenAI GPT-4o | - | 意圖識別、對話生成、SOP 草稿 |
| **Embedding 模型** | OpenAI text-embedding-3-small | - | 文本向量化 (1536 維) |
| **關聯式資料庫** | PostgreSQL | 16 | 主要資料儲存 |
| **向量擴展** | pgvector | 0.7+ | 向量索引與相似度搜尋 |
| **快取** | Redis | 7+ | Session 快取、Rate Limiting |
| **前端框架 (V2.0)** | Next.js (React) | 14+ | 技師 Web App / 管理後台 |
| **前端語言 (V2.0)** | TypeScript | 5+ | 型別安全的前端開發 |
| **Admin UI (V1.0)** | FastAPI + Jinja2 / HTMX | - | 輕量管理後台 |
| **容器化** | Docker + docker-compose | 24+ | 開發與部署環境標準化 |
| **CI/CD** | GitHub Actions | - | 自動化測試與部署流程 |
| **LINE 整合** | line-bot-sdk-python | 3+ | LINE Messaging API 互動 |
| **ORM** | SQLAlchemy | 2.0+ | 非同步資料庫操作 |
| **資料驗證** | Pydantic | 2.0+ | Request/Response 模型驗證 |
| **資料遷移** | Alembic | 1.13+ | 資料庫 Schema 版本管理 |
| **測試框架** | pytest + pytest-asyncio | - | 單元測試與整合測試 |
| **PDF 解析** | PyMuPDF (fitz) | - | 電子鎖手冊 PDF 解析 |

#### 架構決策記錄 (ADR) 索引

所有重大技術決策應記錄為 ADR，存放於 `docs/adrs/` 目錄。

| ADR 編號 | 標題 | 狀態 | 影響範圍 |
| :--- | :--- | :--- | :--- |
| ADR-001 | 選用 FastAPI 作為後端框架 | Accepted | 全系統 |
| ADR-002 | 選用 PostgreSQL + pgvector 作為資料庫與向量儲存 | Accepted | 數據層 |
| ADR-003 | 選用 LangChain + OpenAI GPT-4o 作為 LLM 方案 | Accepted | AI 元件 |
| ADR-004 | V1.0 採用 Modular Monolith 架構 | Accepted | 全系統 |
| ADR-005 | 選用 Redis 作為 Session 與快取方案 | Accepted | 數據層 |
| ADR-006 | Admin UI V1.0 使用 Jinja2 + HTMX，V2.0 遷移至 Next.js | Accepted | 前端 |
| ADR-007 | 採用 Docker Compose 作為部署策略 | Accepted | 基礎設施 |
| ADR-008 | Embedding 模型選用 text-embedding-3-small | Accepted | AI 元件 |

---

## 第 2 部分：需求摘要

### 2.1 功能性需求摘要

#### V1.0 - AI 智能客服

| 需求 ID | 功能模組 | 描述 |
| :--- | :--- | :--- |
| FR-101 | LINE Bot 整合 | 接收 LINE 用戶訊息（文字/圖片/位置），回覆 Flex Message，支援 Rich Menu |
| FR-102 | 多輪對話管理 | 維護對話上下文，支援多輪問診流程，對話超時自動清理 |
| FR-103 | ProblemCard 引擎 | AI 輔助從對話中提取結構化欄位，建立問題卡，識別缺失欄位並追問 |
| FR-104 | 三層解決機制 (L1) | 知識庫精確匹配：向量搜尋 + 關鍵字匹配，命中閾值 >= 0.85 |
| FR-105 | 三層解決機制 (L2) | AI 推理生成：基於 ProblemCard + 手冊段落 + 歷史案例，使用 GPT-4o 生成解決建議 |
| FR-106 | 三層解決機制 (L3) | 轉人工/建立工單：AI 無法解決時，收集客戶資訊準備轉接或建立派工需求 |
| FR-107 | 知識庫管理 | CaseEntry CRUD、PDF 手冊上傳與自動分段、Embedding 批次計算與更新 |
| FR-108 | SOP 自動生成 | 從成功對話中萃取解決模式，自動草擬 SOP，管理員審核後上架 |
| FR-109 | 管理後台 (V1.0) | 知識庫管理介面、對話記錄查詢、ProblemCard 統計、系統健康監控 |
| FR-110 | 用戶意圖識別 | 識別用戶意圖：諮詢 / 報修 / 投訴 / 其他，引導至對應處理流程 |

#### V2.0 - 技師派工與帳務

| 需求 ID | 功能模組 | 描述 |
| :--- | :--- | :--- |
| FR-201 | 技師 Web App | 技師工作台：接單/拒單、工單詳情、導航至現場、服務回報、照片上傳 |
| FR-202 | 智能派工引擎 | 根據技師技能、服務地區、可用時段、評分進行最佳匹配與自動指派 |
| FR-203 | 工單生命週期 | 工單狀態流轉：Created -> Assigned -> Accepted -> InProgress -> Completed -> Closed |
| FR-204 | 計價引擎 | 品牌 x 鎖型 x 難度的計價規則管理，自動報價生成 |
| FR-205 | 帳務系統 | 服務費對帳、發票/請款單管理、月度統計報表 |
| FR-206 | 增強管理後台 | 技師管理、派工監控儀表板、帳務報表、計價規則設定 |
| FR-207 | 通知系統 | LINE 推播通知（派工成功）、Web App 即時通知（新工單） |

### 2.2 非功能性需求

| NFR 分類 | 具體需求描述 | 衡量指標/目標值 | 階段 |
| :--- | :--- | :--- | :--- |
| **AI 準確度** | AI 對電子鎖問題的診斷與解答準確率 | >= 80%（50 題標準測試集） | V1.0 |
| **並發能力** | 系統同時處理的用戶數量 | V1.0: 50 concurrent / V2.0: 100 concurrent | V1.0 / V2.0 |
| **API 延遲** | REST API 端點的回應延遲（不含 LLM 呼叫） | P95 < 2 秒 | V1.0 |
| **LLM 回應延遲** | LLM API 呼叫的端到端延遲 | P95 < 10 秒（含網路） | V1.0 |
| **可用性** | 系統正常運行時間 | >= 99.5%（月度） | V1.0 |
| **資料備份** | 每日自動備份 | 每日 1 次，保留 7 天 | V1.0 |
| **安全性** | 資料傳輸加密 | SSL/TLS (HTTPS) | V1.0 |
| **安全性** | LINE Webhook 驗證 | HMAC-SHA256 簽章驗證 | V1.0 |
| **安全性** | API 認證 | JWT Token（Admin / Technician） | V1.0 / V2.0 |
| **部署** | 標準化部署 | Docker + docker-compose | V1.0 |
| **可維護性** | 程式碼覆蓋率 | >= 70%（核心業務邏輯） | V1.0 |
| **可擴展性** | V1.0 -> V2.0 無需重寫核心 | 模組化架構，新模組可插拔式添加 | V1.0 |

---

## 第 3 部分：高層次架構設計

### 3.1 架構模式

**選定模式：** Modular Monolith (V1.0) -> Microservices-ready (V2.0)

**選擇理由：**

V1.0 採用 **Modular Monolith**（模組化單體）而非微服務，基於以下考量：

1. **團隊規模匹配**：小型團隊（1-3 人），微服務的分散式複雜度遠超收益
2. **部署簡單性**：Docker Compose 單機部署，無需 K8s 等編排系統
3. **開發效率**：模組間可直接呼叫，無需處理服務間通信、分散式事務等問題
4. **V2.0 平滑升級**：透過 Clean Architecture 嚴格的分層與介面抽象，V2.0 新模組（Dispatch, Accounting）可作為新的 Python package 直接加入，或在需要時拆為獨立服務

**模組化策略：**

```
src/
  smartlock/
    customer_service/     # 客服限界上下文 (V1.0)
      domain/
      application/
      infrastructure/
    knowledge_base/       # 知識庫限界上下文 (V1.0)
      domain/
      application/
      infrastructure/
    user_management/      # 使用者管理上下文 (V1.0)
      domain/
      application/
      infrastructure/
    dispatch/             # 派工限界上下文 (V2.0)
      domain/
      application/
      infrastructure/
    accounting/           # 帳務限界上下文 (V2.0)
      domain/
      application/
      infrastructure/
    shared/               # 共享核心
      domain/             # 共用 Value Objects
      infrastructure/     # 共用基礎設施 (DB, Cache, LLM)
```

每個限界上下文是一個獨立的 Python package，有明確的對外介面（Application Service），禁止跨上下文直接存取 Domain 層或 Infrastructure 層。

### 3.2 系統上下文圖

（見 [1.1 L1 系統情境圖](#l1---系統情境圖-system-context-diagram)）

### 3.3 系統組件圖

以下展示整體系統的高層組件互動，包含 V1.0 與 V2.0 的完整視圖：

```mermaid
graph TB
    subgraph "User Interfaces"
        LINE_APP["LINE App<br/>(一般用戶)"]
        TECH_WEB["Technician Web App<br/>(V2.0 - Next.js)"]
        ADMIN_WEB["Admin Panel<br/>(V1.0: Jinja2+HTMX<br/>V2.0: Next.js)"]
    end

    subgraph "External Services"
        LINE_MsgAPI["LINE Messaging API"]
        OpenAI_API["OpenAI API<br/>(GPT-4o + Embeddings)"]
    end

    subgraph "Application Core (FastAPI)"

        subgraph "Interface Adapters"
            WEBHOOK["LINE Webhook<br/>Handler"]
            REST_API["REST API<br/>Controllers"]
            WS["WebSocket<br/>(V2.0 即時通知)"]
        end

        subgraph "V1.0 Modules"
            CONV["Conversation<br/>Manager"]
            PCARD["ProblemCard<br/>Engine"]
            RESOLVER["Three-Layer<br/>Resolver"]
            KB["Knowledge Base<br/>Manager"]
            SOP["SOP<br/>Generator"]
        end

        subgraph "V2.0 Modules"
            DISPATCH["Dispatch<br/>Engine"]
            PRICING["Pricing<br/>Engine"]
            ACCOUNT["Accounting<br/>Module"]
        end

        subgraph "Shared Infrastructure"
            LLM_GW["LLM Gateway<br/>(LangChain)"]
            LINE_SDK["LINE SDK<br/>Adapter"]
            AUTH["Auth<br/>Module"]
        end
    end

    subgraph "Data Stores"
        PG_DB["PostgreSQL 16<br/>+ pgvector"]
        REDIS_DB["Redis"]
    end

    LINE_APP --> LINE_MsgAPI
    LINE_MsgAPI -- "Webhook" --> WEBHOOK
    LINE_SDK --> LINE_MsgAPI

    TECH_WEB --> REST_API
    TECH_WEB --> WS
    ADMIN_WEB --> REST_API

    WEBHOOK --> CONV
    CONV --> PCARD
    CONV --> RESOLVER
    RESOLVER --> KB
    RESOLVER --> SOP
    RESOLVER --> DISPATCH
    CONV --> LINE_SDK

    RESOLVER --> LLM_GW
    PCARD --> LLM_GW
    SOP --> LLM_GW
    KB --> LLM_GW
    LLM_GW --> OpenAI_API

    REST_API --> KB
    REST_API --> DISPATCH
    REST_API --> PRICING
    REST_API --> ACCOUNT
    REST_API --> AUTH

    DISPATCH --> PRICING

    CONV --> PG_DB
    CONV --> REDIS_DB
    PCARD --> PG_DB
    KB --> PG_DB
    DISPATCH --> PG_DB
    PRICING --> PG_DB
    ACCOUNT --> PG_DB
    AUTH --> PG_DB
    AUTH --> REDIS_DB
```

### 3.4 主要組件職責表

| 組件名稱 | 核心職責 | 主要技術 | 依賴 | 階段 |
| :--- | :--- | :--- | :--- | :--- |
| **LINE Webhook Handler** | 接收 LINE 平台的 Webhook 回調事件，驗證 HMAC-SHA256 簽章，解析事件類型（Message, Postback, Follow），路由至對應處理器 | FastAPI, line-bot-sdk | Conversation Manager | V1.0 |
| **Conversation Manager** | 管理對話狀態機（Idle -> Collecting -> Resolving -> Resolved/Escalated），維護多輪對話上下文，Session 超時處理（30 分鐘），訊息收發協調 | Python, Redis | ProblemCard Engine, Three-Layer Resolver, LINE SDK Adapter, Redis | V1.0 |
| **ProblemCard Engine** | 從對話中提取結構化問題描述，AI 輔助欄位推斷（從自然語言中提取 model/location/symptoms），識別缺失欄位並產生追問訊息 | Python, LangChain | LLM Gateway, PostgreSQL | V1.0 |
| **Three-Layer Resolver** | 依序執行三層解決機制：L1 向量搜尋 + 關鍵字匹配 -> L2 GPT-4o 推理（RAG）-> L3 轉人工/建單。記錄解決路徑供 SOP 生成使用 | Python, LangChain | Knowledge Base Manager, LLM Gateway, Dispatch Engine (V2.0) | V1.0 |
| **Knowledge Base Manager** | CaseEntry 與 ManualChunk 的 CRUD 操作，PDF 上傳後自動分段（chunk），Embedding 批次計算與增量更新，向量搜尋介面 | Python, PyMuPDF, pgvector | LLM Gateway (Embedding), PostgreSQL + pgvector | V1.0 |
| **SOP Generator** | 監聽「問題成功解決」事件，分析對話記錄與解決路徑，使用 GPT-4o 草擬 SOP，提交至管理員審核佇列 | Python, LangChain | LLM Gateway, PostgreSQL | V1.0 |
| **LLM Gateway** | LangChain 封裝的 LLM 呼叫統一入口，管理 Prompt Templates，追蹤 Token 使用量，實現 retry/fallback 策略，回應品質過濾 | LangChain, OpenAI SDK | OpenAI API | V1.0 |
| **LINE SDK Adapter** | 封裝 line-bot-sdk-python，提供 Reply Message, Push Message, Flex Message Builder 等便捷介面 | line-bot-sdk-python | LINE Messaging API | V1.0 |
| **Auth Module** | JWT Token 發行與驗證，Admin / Technician 角色區分，API 存取控制 | FastAPI Security, JWT | PostgreSQL, Redis | V1.0 |
| **Admin Panel** | V1.0: Jinja2 + HTMX 的伺服器端渲染管理介面。V2.0: 遷移至 Next.js SPA | V1.0: Jinja2/HTMX, V2.0: Next.js | REST API | V1.0 / V2.0 |
| **Dispatch Engine** | 工單建立與生命週期管理，智能技師匹配（技能/地區/評分/可用時段），派工通知推送 | Python | PostgreSQL, Redis (通知) | V2.0 |
| **Pricing Engine** | 計價規則管理（品牌 x 鎖型 x 難度），自動報價計算，折扣與加成規則 | Python | PostgreSQL | V2.0 |
| **Accounting Module** | 對帳作業，發票/請款單 CRUD，月度統計報表生成，匯出功能 | Python | PostgreSQL | V2.0 |
| **Technician Web App** | 技師端 SPA：工單列表、接單/拒單、到場打卡、服務回報（含照片上傳）、導航整合 | Next.js, TypeScript | REST API, WebSocket | V2.0 |

### 3.5 關鍵用戶旅程

#### 場景 1：用戶透過 LINE 諮詢電子鎖問題（V1.0 核心流程）

**前提：** 用戶已加入 LINE 官方帳號好友

```
1. 用戶 在 LINE App 中發送訊息：「我家的門鎖打不開了」
2. LINE Platform 透過 Webhook POST 將事件發送至 LINE Webhook Handler
3. Webhook Handler 驗證簽章，解析出 MessageEvent (Text)，轉發至 Conversation Manager
4. Conversation Manager 以 LINE user_id 查詢 Redis 中是否有活躍 Session
   - 無 Session -> 建立新 Conversation，狀態設為 Collecting
   - 有 Session -> 載入既有對話上下文
5. Conversation Manager 將用戶訊息傳給 ProblemCard Engine
6. ProblemCard Engine 呼叫 LLM Gateway -> GPT-4o，從訊息中提取：
   - symptoms: "門鎖打不開"
   - intent: "報修"
   - 缺失欄位：model, location, door_status, network
7. ProblemCard Engine 回傳追問訊息：「請問您的電子鎖是哪個品牌和型號？」
8. Conversation Manager 透過 LINE SDK Adapter 將追問以 Flex Message 發送給用戶
9. （多輪對話持續，逐步填充 ProblemCard 欄位）
10. ProblemCard 達到最低完整度 -> Conversation 狀態轉為 Resolving
11. Three-Layer Resolver 啟動：
    - L1: Knowledge Base Manager 以 ProblemCard 內容進行向量搜尋，
          查詢 PostgreSQL + pgvector 中的 CaseEntry，相似度閾值 >= 0.85
    - 命中 -> 回傳解決方案，Conversation 狀態 -> Resolved
    - 未命中 -> 進入 L2
12. L2: Three-Layer Resolver 組裝 RAG 上下文（ProblemCard + 相關 ManualChunk + 近似 CaseEntry），
    呼叫 LLM Gateway -> GPT-4o 生成解決建議
    - 生成品質通過過濾 -> 回傳解決方案，Conversation 狀態 -> Resolved
    - 品質不足 -> 進入 L3
13. L3: 收集客戶聯絡資訊，提示將轉接人工客服或安排技師到場
14. 成功解決後，SOP Generator 非同步監聽 ResolutionFound 事件，
    分析對話與解決路徑，草擬 SOP 待審核
```

#### 場景 2：管理員上傳新的電子鎖手冊 PDF（V1.0 知識庫管理）

```
1. 管理員 登入 Admin Panel (Jinja2 + HTMX)
2. Auth Module 驗證 JWT Token，確認 Admin 角色
3. 管理員 上傳 PDF 檔案至「手冊管理」頁面
4. REST API Controller 接收檔案，轉交 Knowledge Base Manager
5. Knowledge Base Manager 執行以下流程：
   a. PDF 解析：使用 PyMuPDF 提取文本與頁碼
   b. 文本分段：以 500 tokens 為窗口、100 tokens 重疊進行 chunk 分割
   c. 元資料標注：每個 chunk 關聯來源 PDF、頁碼、章節標題
   d. Embedding 計算：呼叫 LLM Gateway -> text-embedding-3-small 批次計算
   e. 入庫：ManualChunk 記錄（含 embedding vector）寫入 PostgreSQL + pgvector
   f. 索引更新：pgvector HNSW 索引自動更新
6. Knowledge Base Manager 回傳處理結果（成功/失敗 chunk 數量）
7. Admin Panel 顯示上傳結果摘要
```

#### 場景 3：技師接收與完成派工單（V2.0 派工流程）

```
1. L3 解決機制觸發工單建立，Three-Layer Resolver 呼叫 Dispatch Engine
2. Dispatch Engine 建立 WorkOrder：
   - 關聯 ProblemCard 資訊
   - 狀態設為 Created
   - 呼叫 Pricing Engine 生成報價
3. Dispatch Engine 執行智能匹配：
   a. 篩選技師：技能涵蓋該鎖型品牌、服務地區涵蓋該地點
   b. 排序：綜合評分 = 0.4 * 技能匹配度 + 0.3 * 距離評分 + 0.3 * 歷史評分
   c. 選出 Top-1 技師，WorkOrder 狀態 -> Assigned
4. Dispatch Engine 透過 WebSocket 即時通知 Technician Web App
5. 技師 在 Web App 看到新工單通知，查看工單詳情（ProblemCard 摘要、客戶地址、預估報價）
6. 技師 接單 -> WorkOrder 狀態 -> Accepted
7. 技師 到場打卡 -> WorkOrder 狀態 -> InProgress
8. 技師 完成服務，上傳照片，填寫服務報告 -> WorkOrder 狀態 -> Completed
9. Dispatch Engine 發布 ServiceCompleted 事件
10. Accounting Module 監聽事件，產生 Invoice/Voucher
11. 管理員 在 Admin Panel 中審核帳務，確認後 WorkOrder 狀態 -> Closed
```

#### 場景 4：知識庫自演化 - SOP 從生成到上架（V1.0 閉環）

```
1. SOP Generator 接收 ResolutionFound 事件
2. SOP Generator 分析該次對話：
   a. 讀取完整 Conversation messages
   b. 讀取 ProblemCard 內容
   c. 識別解決路徑（L1 命中的 CaseEntry 或 L2 生成的方案）
3. SOP Generator 呼叫 LLM Gateway -> GPT-4o，使用專用 Prompt Template：
   - 輸入：ProblemCard + 解決步驟 + 用戶反饋
   - 輸出：結構化 SOP（適用條件、步驟清單、注意事項）
4. SOPDraft 寫入 PostgreSQL，狀態設為 PendingReview
5. Admin Panel 顯示待審核 SOP 列表
6. 管理員 審核 SOPDraft：
   - 通過 -> 轉換為 CaseEntry，計算 Embedding，加入知識庫
   - 修改 -> 管理員編輯後重新提交
   - 拒絕 -> 標記為 Rejected，記錄原因
7. 新 CaseEntry 生效，未來同類問題可在 L1 直接命中
```

---

## 第 4 部分：技術選型詳述

### 4.1 技術選型原則

| 原則 | 說明 |
| :--- | :--- |
| **實用主義優先** | 解決實際問題，拒絕過度設計。技術選型需匹配團隊規模與專案階段 |
| **成熟穩定** | 優先選擇有活躍社群、良好文檔、生產驗證的技術 |
| **團隊技能對齊** | 在滿足需求的前提下，優先選擇團隊熟悉的技術棧 |
| **簡潔部署** | V1.0 階段以 Docker Compose 單機部署為目標，避免引入不必要的基礎設施複雜度 |
| **可演進性** | 架構設計需預留 V2.0 擴展空間，但不提前實現 |

### 4.2 技術棧詳情

| 分類 | 選用技術 | 選擇理由 (Justification) | 考量的備選方案 | 風險/成熟度 | 相關 ADR |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **後端框架** | Python 3.11+ / FastAPI | 1. 原生 async/await 支援，適合 I/O 密集的 LLM 呼叫場景<br/>2. 自動 OpenAPI 文檔生成，降低 API 文檔維護成本<br/>3. Pydantic 整合提供強型別驗證<br/>4. Python 生態在 AI/ML 領域最為豐富 | **Django REST Framework**: 功能全面但較重，async 支援尚不成熟<br/>**Node.js / Express**: 非同步效能佳，但 Python 在 AI 生態更強<br/>**Go / Gin**: 高效能，但 LLM 庫生態不如 Python | 成熟 (Mature) | ADR-001 |
| **LLM 框架** | LangChain 0.2+ | 1. 統一抽象層，便於切換 LLM Provider<br/>2. 內建 Chain/Agent 編排能力<br/>3. RAG pipeline 原生支援<br/>4. Prompt Template 管理<br/>5. 活躍社群與豐富文檔 | **直接使用 OpenAI SDK**: 更輕量，但缺乏抽象層與 RAG 支援<br/>**LlamaIndex**: RAG 專精，但通用性不如 LangChain<br/>**Semantic Kernel**: 微軟出品，Python 支援較弱 | 成熟但迭代快 | ADR-003 |
| **LLM 模型** | OpenAI GPT-4o | 1. 目前最佳的多模態理解能力（可處理用戶上傳的門鎖照片）<br/>2. 中文對話品質優異<br/>3. Function Calling 支援結構化輸出<br/>4. 穩定的 API 可用性 | **Claude 3.5 Sonnet**: 同等級能力，但中文場景資料較少<br/>**Gemini 1.5 Pro**: 長上下文優勢，但 API 穩定度待觀察<br/>**本地部署 LLM**: 延遲低但硬體成本高，品質不及 GPT-4o | 成熟 (Mature) | ADR-003 |
| **Embedding 模型** | text-embedding-3-small | 1. 1536 維向量，平衡精度與成本<br/>2. 每百萬 Token 成本僅 $0.02<br/>3. 與 GPT-4o 同一供應商，降低整合複雜度<br/>4. 支援 dimensions 參數可降維 | **text-embedding-3-large**: 更高精度但成本 6 倍<br/>**Cohere Embed**: 多語言能力強，但增加供應商依賴<br/>**本地 BERT**: 零成本但精度差且需維護 GPU | 成熟 (Mature) | ADR-008 |
| **資料庫** | PostgreSQL 16 + pgvector | 1. 單一資料庫同時提供關聯式與向量儲存，架構最簡<br/>2. pgvector 支援 HNSW 索引，查詢效能滿足需求<br/>3. 團隊熟悉 PostgreSQL<br/>4. 成熟的備份、複製、監控生態 | **PostgreSQL + Pinecone**: 向量搜尋更專業，但增加基礎設施與成本<br/>**PostgreSQL + Milvus**: 自建向量 DB，運維複雜度高<br/>**MongoDB + Atlas Vector**: 文件型 DB，但本專案需要強事務保證 | 成熟 (Mature) | ADR-002 |
| **快取** | Redis 7+ | 1. 對話 Session 暫存（TTL 30 分鐘）<br/>2. Rate Limiting（LINE Webhook 防洪）<br/>3. 極低延遲（< 1ms）<br/>4. 成熟穩定，運維成本低 | **Memcached**: 更簡單但功能不足（無 TTL 精細控制）<br/>**Application Memory Cache**: 不支援多 Worker 共享 | 成熟 (Mature) | ADR-005 |
| **前端 (V2.0)** | Next.js 14+ / TypeScript | 1. React 生態系最成熟的全端框架<br/>2. SSR/SSG 提升首屏載入速度<br/>3. TypeScript 型別安全<br/>4. App Router 簡化路由管理 | **Nuxt.js (Vue)**: 同類框架，但 React 生態更大<br/>**SvelteKit**: 更輕量但生態較小<br/>**純 React SPA**: 無 SSR 支援，SEO 與首屏效能較差 | 成熟 (Mature) | ADR-006 |
| **Admin UI (V1.0)** | Jinja2 + HTMX | 1. 伺服器端渲染，無需前端建置流程<br/>2. HTMX 提供類 SPA 體驗，但不需要 JavaScript 框架<br/>3. V1.0 快速交付，V2.0 再遷移至 Next.js | **直接用 Next.js**: 功能更強，但 V1.0 階段前端工作量太大<br/>**Streamlit**: 快速原型，但自訂性差 | 成熟 (Mature) | ADR-006 |
| **容器化** | Docker + docker-compose | 1. 開發環境與部署環境一致<br/>2. 所有服務（API, DB, Redis）一鍵啟動<br/>3. 團隊熟悉，學習成本為零 | **Kubernetes**: V1.0 階段 overkill<br/>**Podman**: Docker 相容但生態較小 | 成熟 (Mature) | ADR-007 |
| **CI/CD** | GitHub Actions | 1. 與 GitHub 程式碼倉庫無縫整合<br/>2. 社群 Actions 豐富<br/>3. 免費額度足夠小型團隊使用 | **GitLab CI**: 功能強大但需遷移倉庫<br/>**Jenkins**: 靈活但維護成本高 | 成熟 (Mature) | - |
| **LINE 整合** | line-bot-sdk-python 3+ | 1. LINE 官方維護的 Python SDK<br/>2. Webhook 簽章驗證內建<br/>3. Flex Message Builder API | **自行實作 HTTP Client**: 靈活但重複造輪子 | 成熟 (Mature) | - |
| **ORM** | SQLAlchemy 2.0+ (Async) | 1. Python 生態最成熟的 ORM<br/>2. 2.0 版原生 async 支援<br/>3. 靈活的查詢構建能力<br/>4. 搭配 Alembic 做 Schema 遷移 | **Tortoise ORM**: async 原生但生態較小<br/>**SQLModel**: 基於 SQLAlchemy + Pydantic，但功能受限 | 成熟 (Mature) | - |
| **PDF 解析** | PyMuPDF (fitz) | 1. 解析速度快，記憶體效率高<br/>2. 支援文本提取與頁面結構解析<br/>3. 開源免費 | **pdfplumber**: 表格解析強但速度慢<br/>**Apache Tika**: 功能全面但需 Java Runtime | 成熟 (Mature) | - |
| **測試** | pytest + pytest-asyncio | 1. Python 標準測試框架<br/>2. 豐富的插件生態<br/>3. fixture 機制簡化測試資料準備<br/>4. pytest-asyncio 支援 async 測試 | **unittest**: 標準庫但功能較弱 | 成熟 (Mature) | - |

---

## 第 5 部分：數據架構

### 5.1 數據模型

#### ER 圖 (Entity Relationship Diagram)

```mermaid
erDiagram
    %% ===== V1.0 核心實體 =====

    User {
        uuid id PK
        string line_user_id UK "LINE platform user ID"
        string display_name
        string phone "nullable - collected at L3"
        string email "nullable"
        string role "line_user | admin | technician"
        timestamp created_at
        timestamp updated_at
    }

    Conversation {
        uuid id PK
        uuid user_id FK
        string session_id UK "unique session identifier"
        string status "active | collecting | resolving | resolved | escalated | expired"
        jsonb context "multi-turn conversation context"
        int message_count
        timestamp started_at
        timestamp resolved_at "nullable"
        timestamp expired_at "nullable"
        timestamp created_at
        timestamp updated_at
    }

    Message {
        uuid id PK
        uuid conversation_id FK
        string role "user | assistant | system"
        string content_type "text | image | location | flex"
        text content
        jsonb metadata "token usage, latency, etc."
        timestamp created_at
    }

    ProblemCard {
        uuid id PK
        uuid conversation_id FK "one-to-one"
        string brand "nullable - e.g. Yale, Samsung"
        string model "nullable - e.g. YDM-4109"
        string location "nullable - address or area"
        string door_status "nullable - locked | unlocked | jammed | unknown"
        string network_status "nullable - online | offline | unknown"
        text symptoms "user-described symptoms"
        string intent "inquiry | repair | complaint | other"
        string status "incomplete | complete | resolved | escalated"
        float completeness_score "0.0 to 1.0"
        string resolution_level "nullable - L1 | L2 | L3"
        jsonb extracted_fields "AI-extracted raw fields"
        timestamp created_at
        timestamp updated_at
    }

    CaseEntry {
        uuid id PK
        string title
        text problem_description
        text solution
        string brand "nullable - applicable brand"
        string lock_type "nullable - applicable lock type"
        string difficulty "easy | medium | hard"
        vector embedding "1536-dim pgvector"
        string source "manual_input | sop_approved | imported"
        uuid approved_by FK "nullable - admin who approved"
        boolean is_active
        int hit_count "times matched in L1"
        timestamp created_at
        timestamp updated_at
    }

    ManualChunk {
        uuid id PK
        uuid manual_id FK
        string source_pdf "filename of source PDF"
        int page_number
        string chapter_title "nullable"
        text content
        int token_count
        vector embedding "1536-dim pgvector"
        timestamp created_at
    }

    Manual {
        uuid id PK
        string filename
        string brand
        string model "nullable"
        int total_pages
        int total_chunks
        string status "processing | completed | failed"
        uuid uploaded_by FK
        timestamp created_at
    }

    SOPDraft {
        uuid id PK
        uuid source_conversation_id FK "originating conversation"
        string title
        text applicable_conditions "when to apply this SOP"
        jsonb steps "ordered list of solution steps"
        text notes "additional notes / warnings"
        string status "pending_review | approved | rejected | revised"
        uuid reviewed_by FK "nullable"
        text review_comment "nullable"
        timestamp created_at
        timestamp reviewed_at "nullable"
    }

    %% ===== V2.0 擴展實體 =====

    Technician {
        uuid id PK
        uuid user_id FK "links to User"
        string name
        string phone
        string email
        jsonb capabilities "list of brand/lock_type skills"
        jsonb service_regions "list of serviceable areas"
        jsonb availability "weekly schedule slots"
        float rating "1.0 to 5.0"
        int completed_orders
        string status "active | inactive | suspended"
        timestamp created_at
        timestamp updated_at
    }

    WorkOrder {
        uuid id PK
        uuid problem_card_id FK
        uuid technician_id FK "nullable until assigned"
        uuid created_by FK "system or admin"
        string status "created | assigned | accepted | rejected | in_progress | completed | closed | cancelled"
        string priority "low | medium | high | urgent"
        text customer_name
        string customer_phone
        string customer_address
        timestamp scheduled_at "nullable"
        timestamp accepted_at "nullable"
        timestamp started_at "nullable"
        timestamp completed_at "nullable"
        text service_report "nullable - technician's report"
        jsonb photos "nullable - uploaded photo URLs"
        float estimated_price
        float final_price "nullable"
        timestamp created_at
        timestamp updated_at
    }

    PriceRule {
        uuid id PK
        string brand
        string lock_type
        string difficulty "easy | medium | hard"
        float base_price
        float labor_cost
        float parts_cost "nullable"
        jsonb modifiers "surcharges, discounts, etc."
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    Invoice {
        uuid id PK
        uuid work_order_id FK
        string invoice_number UK
        float amount
        float tax
        float total
        string status "draft | issued | paid | cancelled"
        jsonb line_items "service breakdown"
        timestamp issued_at "nullable"
        timestamp paid_at "nullable"
        timestamp created_at
        timestamp updated_at
    }

    %% ===== Relationships =====

    User ||--o{ Conversation : "initiates"
    Conversation ||--o{ Message : "contains"
    Conversation ||--|| ProblemCard : "produces"
    Conversation ||--o| SOPDraft : "generates"
    Manual ||--o{ ManualChunk : "split into"
    User ||--o| Technician : "is a (V2.0)"
    ProblemCard ||--o| WorkOrder : "escalates to (V2.0)"
    Technician ||--o{ WorkOrder : "assigned to (V2.0)"
    WorkOrder ||--o| Invoice : "produces (V2.0)"
```

#### 表格索引策略

| 表 | 索引名稱 | 欄位 | 類型 | 用途 |
| :--- | :--- | :--- | :--- | :--- |
| `conversations` | `idx_conv_user_status` | `(user_id, status)` | B-tree | 查詢用戶活躍對話 |
| `conversations` | `idx_conv_session` | `(session_id)` | B-tree (Unique) | Session 查詢 |
| `messages` | `idx_msg_conv_created` | `(conversation_id, created_at)` | B-tree | 對話訊息時序查詢 |
| `problem_cards` | `idx_pc_status` | `(status)` | B-tree | 按狀態篩選問題卡 |
| `problem_cards` | `idx_pc_brand_model` | `(brand, model)` | B-tree | 按品牌型號篩選 |
| `case_entries` | `idx_ce_embedding` | `(embedding)` | HNSW (pgvector) | 向量相似度搜尋 |
| `case_entries` | `idx_ce_brand_active` | `(brand, is_active)` | B-tree | 品牌篩選 + 啟用狀態 |
| `manual_chunks` | `idx_mc_embedding` | `(embedding)` | HNSW (pgvector) | 向量相似度搜尋 |
| `manual_chunks` | `idx_mc_manual` | `(manual_id)` | B-tree | 按手冊查詢 chunks |
| `work_orders` | `idx_wo_tech_status` | `(technician_id, status)` | B-tree | 技師工單查詢 |
| `work_orders` | `idx_wo_status_priority` | `(status, priority)` | B-tree | 待派工工單排序 |
| `invoices` | `idx_inv_wo` | `(work_order_id)` | B-tree | 工單帳務查詢 |

### 5.2 數據流圖

#### 用戶諮詢的數據流

```mermaid
graph LR
    subgraph "Input"
        LM["LINE Message<br/>(text/image/location)"]
    end

    subgraph "Processing Pipeline"
        WH["Webhook Handler<br/>Parse & Validate"]
        CM["Conversation Manager<br/>Load/Create Session"]
        PCE["ProblemCard Engine<br/>Extract Fields (LLM)"]
        L1["L1: Vector Search<br/>(pgvector cosine similarity)"]
        L2["L2: AI Reasoning<br/>(RAG - GPT-4o)"]
        L3["L3: Escalation<br/>(Human / WorkOrder)"]
    end

    subgraph "Data Stores"
        REDIS["Redis<br/>Session Cache"]
        PG_CONV["PostgreSQL<br/>conversations, messages"]
        PG_PC["PostgreSQL<br/>problem_cards"]
        PG_KB["PostgreSQL + pgvector<br/>case_entries, manual_chunks"]
        PG_WO["PostgreSQL<br/>work_orders (V2.0)"]
    end

    subgraph "Output"
        REPLY["LINE Reply<br/>(Flex Message)"]
    end

    LM --> WH
    WH --> CM
    CM -->|"R/W session"| REDIS
    CM -->|"save messages"| PG_CONV
    CM --> PCE
    PCE -->|"save/update"| PG_PC
    PCE --> L1
    L1 -->|"vector query"| PG_KB
    L1 -->|"hit"| REPLY
    L1 -->|"miss"| L2
    L2 -->|"RAG context"| PG_KB
    L2 -->|"resolved"| REPLY
    L2 -->|"unresolved"| L3
    L3 -->|"create order"| PG_WO
    L3 --> REPLY
```

### 5.3 數據一致性策略

本系統為 Modular Monolith，所有模組共享同一個 PostgreSQL 實例，因此：

| 場景 | 一致性需求 | 策略 | 說明 |
| :--- | :--- | :--- | :--- |
| **Conversation + ProblemCard 建立** | 強一致性 | PostgreSQL Transaction | 對話與問題卡必須原子性寫入，使用 SQLAlchemy 的 Session Transaction |
| **CaseEntry 更新 + Embedding 計算** | 最終一致性 | 非同步任務 | Embedding 計算是 I/O 密集操作（呼叫 OpenAI API），允許短暫延遲。先寫入 CaseEntry，再異步計算 Embedding 並回寫 |
| **WorkOrder 建立 + 技師通知** | 最終一致性 | 事件驅動 | 工單寫入 DB 成功後發布 Domain Event，通知模組非同步推送 |
| **WorkOrder 完成 + Invoice 建立** | 強一致性 | PostgreSQL Transaction | 服務完成確認與帳務記錄必須原子性寫入 |
| **Session Cache (Redis) + DB** | 最終一致性 | Cache-Aside Pattern | Redis 作為快取層，DB 為最終事實來源。Session 過期或丟失時從 DB 重建 |

**備份策略：**

- 每日 01:00 AM (UTC+8) 執行 `pg_dump` 全量備份
- 備份檔案保留 7 天，超過自動清理
- 備份檔案壓縮後存放至獨立的備份目錄（或 S3 bucket）
- 每月執行一次備份恢復驗證

### 5.4 向量索引策略

#### pgvector 配置

| 參數 | 值 | 說明 |
| :--- | :--- | :--- |
| **向量維度** | 1536 | text-embedding-3-small 輸出維度 |
| **索引類型** | HNSW | 查詢效能優於 IVFFlat，無需訓練，適合增量更新 |
| **距離函數** | cosine | 語義相似度搜尋的標準選擇 |
| **HNSW m** | 16 | 每層最大連接數，平衡精度與建索引速度 |
| **HNSW ef_construction** | 64 | 建索引時的搜尋寬度，越高越精確但越慢 |
| **ef_search** | 40 | 查詢時的搜尋寬度，runtime 可調整 |

#### 索引建立 SQL

```sql
-- CaseEntry 向量索引
CREATE INDEX idx_case_entry_embedding ON case_entries
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- ManualChunk 向量索引
CREATE INDEX idx_manual_chunk_embedding ON manual_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 查詢時設定 ef_search
SET hnsw.ef_search = 40;
```

#### 搜尋策略

```
L1 解決機制的向量搜尋流程：

1. 將 ProblemCard 的 symptoms + brand + model 組合為查詢文本
2. 呼叫 Embedding API 計算查詢向量
3. 兩路查詢：
   a. CaseEntry 向量搜尋 (cosine similarity, top-5)
   b. ManualChunk 向量搜尋 (cosine similarity, top-5)
4. 合併結果，以相似度分數排序
5. 最高分 >= 0.85 -> L1 命中
6. 0.70 <= 最高分 < 0.85 -> 作為 L2 RAG 上下文
7. 最高分 < 0.70 -> 標記為低信心，仍傳給 L2 參考
```

#### 資料量預估與效能

| 指標 | 預估值 (V1.0 上線後 6 個月) | 說明 |
| :--- | :--- | :--- |
| CaseEntry 數量 | 500 - 2,000 筆 | 初始導入 + SOP 審核上架 |
| ManualChunk 數量 | 5,000 - 20,000 筆 | 取決於上傳的 PDF 手冊數量 |
| 向量索引記憶體 | ~100 MB | 每個 1536 維 float32 向量約 6KB，20K 筆約 120MB |
| 單次向量搜尋延遲 | < 10ms | HNSW 在此規模下查詢極快 |
| Embedding 計算延遲 | ~200ms / 次 | OpenAI API 呼叫（含網路） |

---

## 第 6 部分：部署與基礎設施

### 6.1 部署視圖

系統使用 Docker Compose 進行容器化部署。以下展示生產環境的部署拓撲：

```mermaid
graph TB
    subgraph "Host Machine (VPS / Cloud VM)"
        subgraph "Docker Network: smartlock-net"

            subgraph "Reverse Proxy"
                NGINX["Nginx<br/>---<br/>SSL Termination<br/>Reverse Proxy<br/>Static File Serving<br/>Rate Limiting<br/>---<br/>Port: 80, 443"]
            end

            subgraph "Application Tier"
                API1["FastAPI App<br/>(Worker 1)<br/>---<br/>Uvicorn<br/>Port: 8000"]
                API2["FastAPI App<br/>(Worker 2)<br/>---<br/>Uvicorn<br/>Port: 8001"]
            end

            subgraph "Frontend Tier (V2.0)"
                NEXT["Next.js App<br/>---<br/>SSR / Static<br/>Port: 3000"]
            end

            subgraph "Data Tier"
                PG["PostgreSQL 16<br/>+ pgvector<br/>---<br/>Port: 5432<br/>Volume: pg_data"]
                RD["Redis 7<br/>---<br/>Port: 6379<br/>Volume: redis_data"]
            end

            subgraph "Utility"
                BACKUP["Backup CronJob<br/>---<br/>Daily pg_dump<br/>Volume: backup_data"]
            end
        end
    end

    subgraph "External"
        INTERNET["Internet<br/>(LINE Users / Admins / Technicians)"]
        LINE_SRV["LINE Platform"]
        OPENAI_SRV["OpenAI API"]
    end

    INTERNET -- "HTTPS :443" --> NGINX
    LINE_SRV -- "Webhook POST :443" --> NGINX
    NGINX -- "Proxy Pass :8000/8001" --> API1
    NGINX -- "Proxy Pass :8000/8001" --> API2
    NGINX -- "Proxy Pass :3000" --> NEXT
    NEXT -- "API Call :8000" --> API1
    API1 -- "SQL :5432" --> PG
    API2 -- "SQL :5432" --> PG
    API1 -- "Cache :6379" --> RD
    API2 -- "Cache :6379" --> RD
    API1 -- "HTTPS" --> OPENAI_SRV
    API2 -- "HTTPS" --> OPENAI_SRV
    API1 -- "HTTPS" --> LINE_SRV
    BACKUP -- "pg_dump :5432" --> PG
```

#### docker-compose.yml 服務定義

| 服務名稱 | Image | 端口 | 環境變數 | Volume | 備註 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `nginx` | nginx:alpine | 80, 443 | - | `./nginx/conf.d`, `./certs` | SSL 終止、反向代理 |
| `api` | 自建 Dockerfile | 8000 (internal) | `DATABASE_URL`, `REDIS_URL`, `OPENAI_API_KEY`, `LINE_CHANNEL_SECRET`, `LINE_CHANNEL_ACCESS_TOKEN`, `JWT_SECRET` | `./uploads` | 可用 `--scale api=2` 水平擴展 |
| `web` (V2.0) | 自建 Dockerfile | 3000 (internal) | `NEXT_PUBLIC_API_URL` | - | Next.js SSR |
| `postgres` | postgres:16-alpine | 5432 (internal) | `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | `pg_data` | 啟用 pgvector extension |
| `redis` | redis:7-alpine | 6379 (internal) | - | `redis_data` | 持久化 appendonly |
| `backup` | postgres:16-alpine | - | - | `backup_data` | cron 排程 pg_dump |

### 6.2 CI/CD 流程

```mermaid
graph LR
    subgraph "Developer"
        DEV["git push<br/>to feature branch"]
    end

    subgraph "GitHub Actions Pipeline"
        subgraph "PR Pipeline"
            LINT["Step 1: Lint<br/>---<br/>ruff check<br/>mypy type check"]
            TEST["Step 2: Test<br/>---<br/>pytest<br/>(unit + integration)<br/>coverage >= 70%"]
            BUILD["Step 3: Build<br/>---<br/>docker build<br/>image validation"]
        end

        subgraph "Main Pipeline (after merge)"
            TAG["Step 4: Tag<br/>---<br/>Semantic Version<br/>Git Tag"]
            PUSH["Step 5: Push Image<br/>---<br/>Push to<br/>Container Registry"]
            DEPLOY["Step 6: Deploy<br/>---<br/>SSH + docker-compose pull<br/>Rolling restart"]
            SMOKE["Step 7: Smoke Test<br/>---<br/>Health check<br/>API validation"]
        end
    end

    subgraph "Production"
        PROD["Production Server<br/>docker-compose up"]
    end

    DEV --> LINT
    LINT -->|pass| TEST
    TEST -->|pass| BUILD
    BUILD -->|merge to main| TAG
    TAG --> PUSH
    PUSH --> DEPLOY
    DEPLOY --> SMOKE
    SMOKE --> PROD
```

#### CI/CD 詳細步驟

| 步驟 | 觸發條件 | 工具 | 動作 | 失敗處理 |
| :--- | :--- | :--- | :--- | :--- |
| **Lint** | PR opened / push | `ruff`, `mypy` | 程式碼風格檢查、型別檢查 | 阻擋 PR merge |
| **Test** | PR opened / push | `pytest`, `pytest-cov` | 單元測試 + 整合測試，覆蓋率門檻 70% | 阻擋 PR merge |
| **Build** | PR opened / push | `docker build` | 驗證 Docker Image 可成功建置 | 阻擋 PR merge |
| **Tag** | merge to main | GitHub Actions | 自動生成語義化版本 Tag | 手動介入 |
| **Push Image** | tag created | Docker Registry | 推送帶版本 Tag 的 Image | 重試 3 次 |
| **Deploy** | image pushed | SSH + docker-compose | `docker-compose pull && docker-compose up -d` | 回滾至前一版本 |
| **Smoke Test** | deploy completed | curl + custom script | 健康檢查端點、關鍵 API 驗證 | 自動回滾 + 告警 |

### 6.3 環境策略

| 環境 | 用途 | 基礎設施 | 資料 | 外部服務 |
| :--- | :--- | :--- | :--- | :--- |
| **Development** | 本地開發與除錯 | Docker Compose (local) | SQLite / PostgreSQL (local)，Mock 資料 | LINE Bot: 使用 ngrok 暫時隧道。OpenAI: 開發帳號（設定用量上限） |
| **Staging** | 整合測試、UAT 驗收 | Docker Compose (VPS) | PostgreSQL (staging)，匿名化生產資料副本 | LINE Bot: 獨立的 Staging Channel。OpenAI: 開發帳號 |
| **Production** | 正式運行環境 | Docker Compose (VPS/Cloud) | PostgreSQL (production)，每日備份 | LINE Bot: 正式 Channel。OpenAI: 正式帳號 |

**環境隔離原則：**
- 每個環境使用獨立的 `.env` 檔案，絕不共享密鑰
- Staging 與 Production 使用獨立的 LINE Channel
- 生產 API Key 僅存在於生產環境的密鑰管理中
- 開發環境使用 OpenAI 帳號的用量上限 (usage cap) 防止誤用

---

## 第 7 部分：跨領域考量

### 7.1 可觀測性

#### 日誌 (Logging)

| 項目 | 規範 |
| :--- | :--- |
| **格式** | JSON 結構化日誌 |
| **框架** | Python `structlog` |
| **等級** | DEBUG (dev) / INFO (staging, prod) |
| **必含欄位** | `timestamp`, `level`, `message`, `request_id`, `user_id` (if available), `module` |
| **LLM 呼叫日誌** | 記錄 prompt_tokens, completion_tokens, total_cost, latency_ms, model, resolution_level |
| **敏感資料** | 日誌中禁止記錄用戶完整訊息內容（僅記錄 message_id 與 content_type） |
| **收集方式** | V1.0: Docker logs + log rotation。V2.0: 可接入 Loki / ELK |
| **保留期限** | 30 天（INFO+）/ 7 天（DEBUG） |

**日誌範例：**

```json
{
  "timestamp": "2026-02-17T10:30:45.123+08:00",
  "level": "INFO",
  "message": "L1 resolution hit",
  "request_id": "req_abc123",
  "user_id": "U1234567890",
  "module": "three_layer_resolver",
  "conversation_id": "conv_xyz",
  "resolution_level": "L1",
  "case_entry_id": "ce_456",
  "similarity_score": 0.92,
  "latency_ms": 45
}
```

#### 指標 (Metrics)

| 指標類別 | 指標名稱 | 類型 | 說明 |
| :--- | :--- | :--- | :--- |
| **API 效能** | `api_request_duration_seconds` | Histogram | API 請求延遲分佈 |
| **API 效能** | `api_request_total` | Counter | API 請求總數（按 method, path, status） |
| **LLM 效能** | `llm_call_duration_seconds` | Histogram | LLM API 呼叫延遲 |
| **LLM 效能** | `llm_token_usage_total` | Counter | Token 使用量（按 model, type） |
| **LLM 成本** | `llm_cost_usd_total` | Counter | LLM 累計花費（USD） |
| **解決率** | `resolution_total` | Counter | 問題解決次數（按 level: L1/L2/L3） |
| **解決率** | `resolution_success_rate` | Gauge | 各層解決成功率 |
| **知識庫** | `knowledge_base_entries_total` | Gauge | CaseEntry 和 ManualChunk 總數 |
| **系統健康** | `active_conversations` | Gauge | 當前活躍對話數 |
| **系統健康** | `db_connection_pool_usage` | Gauge | 資料庫連線池使用率 |
| **V2.0 派工** | `work_order_total` | Counter | 工單數量（按 status） |
| **V2.0 派工** | `dispatch_match_duration_seconds` | Histogram | 技師匹配延遲 |

**指標實現：** V1.0 使用 FastAPI middleware 收集基礎 API 指標，提供 `/metrics` 端點。可選接入 Prometheus + Grafana。

#### 告警 (Alerting)

| 告警名稱 | 條件 | 嚴重度 | 通知管道 |
| :--- | :--- | :--- | :--- |
| API 高延遲 | P95 > 5s 持續 5 分鐘 | P2 - Warning | LINE 群組通知 |
| API 錯誤率飆升 | 5xx 比率 > 5% 持續 3 分鐘 | P1 - Critical | LINE 群組通知 + 電話 |
| LLM 呼叫失敗 | 連續失敗 > 3 次 | P1 - Critical | LINE 群組通知 |
| 資料庫連線耗盡 | 連線池 > 90% | P2 - Warning | LINE 群組通知 |
| 磁碟使用率 | > 85% | P2 - Warning | LINE 群組通知 |
| 備份失敗 | 每日備份未在預期時間完成 | P1 - Critical | LINE 群組通知 + Email |

### 7.2 安全性

#### 威脅分析與防護

| 威脅類別 | 具體威脅 | 風險等級 | 防護措施 |
| :--- | :--- | :--- | :--- |
| **Prompt Injection** | 惡意用戶透過對話注入指令，操控 AI 行為 | 高 | 1. System Prompt 與 User Input 嚴格分離<br/>2. LLM 輸出過濾（禁止敏感內容）<br/>3. 輸入長度限制（單條訊息 < 2000 字元）<br/>4. 定期進行紅隊測試 |
| **Prompt Leaking** | 用戶試圖誘導 AI 洩露 System Prompt 內容 | 中 | 1. System Prompt 中加入反洩露指令<br/>2. 輸出檢測：正則匹配 Prompt 關鍵片段<br/>3. 日誌監控異常對話模式 |
| **LINE Webhook 偽造** | 攻擊者偽造 LINE Webhook 請求 | 高 | 1. 每次 Webhook 請求驗證 HMAC-SHA256 簽章<br/>2. 拒絕簽章不匹配的請求<br/>3. Rate Limiting（Nginx 層） |
| **API 未授權存取** | 未認證用戶存取管理 API 或技師 API | 高 | 1. JWT Token 認證<br/>2. Role-Based Access Control (RBAC)<br/>3. Token 過期時間：Admin 4h / Technician 8h |
| **SQL Injection** | 惡意輸入導致 SQL 注入 | 高 | 1. SQLAlchemy ORM 參數化查詢（禁止原生 SQL 拼接）<br/>2. 輸入驗證（Pydantic schema）<br/>3. 資料庫帳號最小權限原則 |
| **API Key 洩露** | OpenAI / LINE API Key 被洩露 | 高 | 1. 環境變數存放，不提交至版本控制<br/>2. `.env` 在 `.gitignore` 中<br/>3. 定期輪替 Key<br/>4. 設定 OpenAI 用量上限 |
| **DDoS / 濫用** | 惡意大量請求導致系統癱瘓 | 中 | 1. Nginx Rate Limiting（IP 級別）<br/>2. Redis 實現 API Rate Limiting（用戶級別）<br/>3. LINE Webhook 頻率監控 |
| **資料竊取** | 資料庫或備份檔案被盜取 | 中 | 1. 資料庫僅在 Docker 內部網路暴露<br/>2. 備份檔案加密<br/>3. SSL/TLS 傳輸加密<br/>4. VPS 防火牆只開放 80/443 |

#### 認證與授權架構

```
認證流程：
  LINE 用戶 -> 無需額外認證，以 LINE user_id 識別
  管理員    -> JWT Token（/auth/login endpoint）
  技師      -> JWT Token（/auth/login endpoint）

授權模型 (RBAC)：
  Role: line_user
    - 僅透過 LINE Webhook 互動，無直接 API 存取
  Role: admin
    - 知識庫 CRUD
    - SOP 審核
    - 對話記錄查詢
    - 系統設定
    - V2.0: 技師管理、派工監控、帳務管理
  Role: technician (V2.0)
    - 查看指派給自己的工單
    - 接單/拒單
    - 服務回報
    - 查看自己的帳務
```

#### 密鑰管理

| 密鑰 | 儲存方式 | 存取方式 | 輪替策略 |
| :--- | :--- | :--- | :--- |
| `OPENAI_API_KEY` | `.env` 檔案（不入版本控制） | 環境變數 | 每季度輪替 |
| `LINE_CHANNEL_SECRET` | `.env` 檔案 | 環境變數 | LINE 後台設定，按需輪替 |
| `LINE_CHANNEL_ACCESS_TOKEN` | `.env` 檔案 | 環境變數 | LINE 後台設定，按需輪替 |
| `JWT_SECRET` | `.env` 檔案 | 環境變數 | 每季度輪替 |
| `DATABASE_URL` | `.env` 檔案 | 環境變數 | 密碼每季度輪替 |
| `REDIS_URL` | `.env` 檔案 | 環境變數 | 按需設定 |

---

## 第 8 部分：風險與緩解策略

| 風險類別 | 風險描述 | 可能性 | 影響程度 | 緩解策略 |
| :--- | :--- | :--- | :--- | :--- |
| **AI 品質** | GPT-4o 對特定品牌/型號的電子鎖問題診斷不準確，低於 80% 目標 | 中 | 高 | 1. 建立 50 題標準測試集，持續追蹤準確率<br/>2. 持續豐富知識庫（案例 + 手冊），提升 L1 命中率<br/>3. Prompt Engineering 迭代優化<br/>4. SOP 自演化機制持續改善知識品質 |
| **LLM API 依賴** | OpenAI API 故障或回應延遲過高，導致系統功能降級 | 低 | 高 | 1. LangChain 抽象層允許快速切換 Provider（如 Azure OpenAI）<br/>2. L1（知識庫搜尋）不依賴 LLM API，可獨立運作<br/>3. 設定 timeout (30s) + retry (3 次 exponential backoff)<br/>4. 降級策略：LLM 不可用時回退至 L1 + L3 |
| **LLM 成本** | 用戶量增長導致 OpenAI API 費用超出預算 | 中 | 中 | 1. 使用較便宜的 text-embedding-3-small（$0.02/M tokens）<br/>2. L1 命中率越高，L2 LLM 呼叫越少<br/>3. Redis 快取相同問題的回覆（TTL 24h）<br/>4. 監控 Token 使用量，設定每日/每月告警閾值 |
| **Prompt Injection** | 惡意用戶注入指令導致 AI 產生不當回應 | 中 | 高 | 1. System Prompt 硬化（角色固定、範圍限制）<br/>2. 輸出過濾（敏感詞檢測、格式驗證）<br/>3. 輸入長度限制<br/>4. 定期紅隊測試 |
| **資料安全** | 資料庫洩露或備份檔案被盜 | 低 | 高 | 1. 資料庫不暴露外部端口<br/>2. 備份加密<br/>3. VPS 防火牆嚴格配置<br/>4. 定期安全審計 |
| **V1 -> V2 升級風險** | V2.0 模組（Dispatch/Accounting）與 V1.0 核心模組整合時產生衝突 | 中 | 中 | 1. Clean Architecture 確保模組間依賴透過介面抽象<br/>2. 限界上下文邊界清晰<br/>3. V2.0 模組作為新 package 加入，不修改 V1.0 核心程式碼<br/>4. 充分的整合測試 |
| **LINE 平台限制** | LINE Messaging API 的 Reply Token 有效期僅 30 秒，LLM 回應可能超時 | 中 | 中 | 1. 先回覆「處理中」訊息（使用 Reply Token）<br/>2. LLM 完成後使用 Push Message 發送結果<br/>3. Push Message 有免費額度限制，監控使用量 |
| **團隊風險** | 小型團隊（1-3 人），關鍵人離開導致專案停滯 | 低 | 高 | 1. 完善的技術文檔（本文件）<br/>2. 程式碼註解與 Docstring<br/>3. 標準化的開發流程與 CI/CD<br/>4. 定期知識分享 |
| **效能瓶頸** | 並發用戶超過預期，單機 Docker Compose 部署無法承受 | 低 | 中 | 1. V1.0 目標僅 50 concurrent，Docker Compose 足夠<br/>2. FastAPI + Uvicorn 可水平擴展（`--scale api=N`）<br/>3. PostgreSQL 連線池管理（asyncpg + pgbouncer 備案）<br/>4. Redis 分擔熱點查詢壓力 |

---

## 第 9 部分：架構演進路線圖

```mermaid
gantt
    title 架構演進時間線
    dateFormat  YYYY-MM
    axisFormat  %Y-%m

    section V1.0 AI 智能客服
    核心基礎建設 (FastAPI + DB + Redis)           :v1_infra, 2026-03, 2026-04
    LINE Bot + Webhook + 對話管理                  :v1_line, 2026-04, 2026-05
    ProblemCard Engine + Three-Layer Resolver       :v1_core, 2026-05, 2026-07
    知識庫管理 + Embedding + 向量搜尋              :v1_kb, 2026-06, 2026-07
    SOP Generator + Admin Panel (Jinja2+HTMX)      :v1_admin, 2026-07, 2026-08
    V1.0 上線與優化                                :v1_launch, 2026-08, 2026-09

    section V2.0 派工與帳務
    Next.js 前端 + Admin Panel 遷移               :v2_fe, 2026-09, 2026-11
    Dispatch Engine + Technician Web App           :v2_dispatch, 2026-10, 2026-12
    Pricing Engine + Accounting Module             :v2_acc, 2026-11, 2027-01
    V2.0 上線與整合測試                           :v2_launch, 2027-01, 2027-02

    section 未來展望
    多租戶 SaaS 支援                              :future_mt, 2027-03, 2027-06
    行動端原生 App (React Native)                  :future_app, 2027-06, 2027-09
```

### V1.0 - AI 智能客服（目標：2026 Q3 上線）

| 里程碑 | 交付物 | 架構重點 |
| :--- | :--- | :--- |
| M1: 基礎建設 | FastAPI skeleton, PostgreSQL + pgvector, Redis, Docker Compose, CI/CD | 建立 Clean Architecture 分層結構，定義模組邊界 |
| M2: LINE Bot 核心 | Webhook Handler, Conversation Manager, Session 管理 | 對話狀態機設計，Redis Session 管理 |
| M3: AI 問診引擎 | ProblemCard Engine, Three-Layer Resolver, LLM Gateway | LangChain 整合，Prompt Template 設計，RAG pipeline |
| M4: 知識庫 | CaseEntry/ManualChunk CRUD, PDF Parser, Embedding Pipeline | pgvector HNSW 索引，批次 Embedding 計算 |
| M5: 自演化 + 管理 | SOP Generator, Admin Panel | 事件驅動的 SOP 生成，Jinja2 + HTMX 管理介面 |
| M6: 上線 | 部署、監控、備份 | Nginx SSL, 日誌收集, 備份排程 |

### V2.0 - 技師派工與帳務（目標：2027 Q1 上線）

| 里程碑 | 交付物 | 架構重點 |
| :--- | :--- | :--- |
| M7: 前端升級 | Next.js Admin Panel, 共用元件庫 | Admin Panel 從 Jinja2 遷移至 Next.js |
| M8: 派工系統 | Dispatch Engine, Technician Web App, WorkOrder 管理 | 新的 Dispatch 限界上下文，WebSocket 即時通知 |
| M9: 帳務系統 | Pricing Engine, Invoice, Accounting Report | 新的 Accounting 限界上下文，報表匯出 |
| M10: 整合上線 | 全功能整合測試, 效能壓力測試 | 端到端測試，並發 100 用戶壓力測試 |

### 未來展望（V3.0+）

| 方向 | 說明 | 架構影響 |
| :--- | :--- | :--- |
| **多租戶 SaaS** | 支援多個電子鎖品牌商各自獨立的知識庫與管理後台 | 資料隔離策略（Schema-per-tenant 或 Row-level），租戶路由 |
| **行動端 App** | 技師端 React Native App，替代 Web App | API 層已準備好，新增 App-specific endpoints |
| **微服務拆分** | 若規模增長至需要獨立擴展某些模組 | Modular Monolith 的模組邊界已劃清，可按需拆分為獨立服務 |
| **本地 LLM** | 部署開源 LLM 降低 API 費用 | LangChain 抽象層允許切換，需評估 GPU 基礎設施成本 |
| **語音支援** | LINE 語音訊息 -> Speech-to-Text -> AI 處理 | 增加 STT 模組，接入 Whisper API |
| **IoT 整合** | 直接讀取電子鎖裝置狀態（電量、連線、錯誤碼） | 新增 IoT Gateway 模組，MQTT/HTTP 整合 |

---

## 第 10 部分：附錄

### 附錄 A：專案目錄結構

```
Smart-Lock_AI_Support_Service_Dispatch_SaaS_Platform/
├── docs/                           # 專案文檔
│   ├── 05_architecture_and_design_document.md   # 本文件
│   └── adrs/                       # 架構決策記錄
│       ├── ADR-001_backend_framework.md
│       ├── ADR-002_database_selection.md
│       └── ...
├── src/
│   └── smartlock/                  # 核心應用程式碼
│       ├── __init__.py
│       ├── main.py                 # FastAPI app entry point
│       ├── config.py               # 設定管理
│       ├── customer_service/       # 客服限界上下文
│       │   ├── domain/
│       │   │   ├── entities.py     # Conversation, ProblemCard, Message
│       │   │   ├── value_objects.py
│       │   │   ├── events.py       # Domain Events
│       │   │   └── services.py     # ThreeLayerResolutionPolicy
│       │   ├── application/
│       │   │   ├── conversation_service.py
│       │   │   ├── problem_card_service.py
│       │   │   ├── resolution_service.py
│       │   │   ├── dto.py
│       │   │   └── ports.py        # Abstract interfaces
│       │   └── infrastructure/
│       │       ├── webhook_controller.py
│       │       ├── conversation_repo.py
│       │       ├── line_adapter.py
│       │       └── llm_gateway.py
│       ├── knowledge_base/         # 知識庫限界上下文
│       │   ├── domain/
│       │   ├── application/
│       │   └── infrastructure/
│       ├── user_management/        # 使用者管理上下文
│       │   ├── domain/
│       │   ├── application/
│       │   └── infrastructure/
│       ├── dispatch/               # 派工上下文 (V2.0)
│       │   ├── domain/
│       │   ├── application/
│       │   └── infrastructure/
│       ├── accounting/             # 帳務上下文 (V2.0)
│       │   ├── domain/
│       │   ├── application/
│       │   └── infrastructure/
│       └── shared/                 # 共享基礎設施
│           ├── database.py         # SQLAlchemy engine & session
│           ├── redis.py            # Redis client
│           ├── auth.py             # JWT auth utilities
│           ├── logging.py          # Structured logging setup
│           └── middleware.py       # CORS, request ID, timing
├── tests/
│   ├── unit/
│   │   ├── customer_service/
│   │   ├── knowledge_base/
│   │   └── ...
│   ├── integration/
│   │   ├── test_line_webhook.py
│   │   ├── test_resolution_flow.py
│   │   └── ...
│   └── conftest.py                # Shared fixtures
├── migrations/                     # Alembic 資料庫遷移
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
├── templates/                      # Jinja2 templates (V1.0 Admin)
├── static/                         # Static assets (V1.0 Admin)
├── web/                            # Next.js frontend (V2.0)
│   ├── src/
│   ├── package.json
│   └── next.config.js
├── docker/
│   ├── Dockerfile.api
│   ├── Dockerfile.web
│   └── nginx/
│       └── conf.d/
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
├── .gitignore
├── pyproject.toml                  # Python project config (Poetry)
├── README.md
└── Makefile                        # Common dev commands
```

### 附錄 B：關鍵 API 端點概覽

| 方法 | 路徑 | 說明 | 認證 | 階段 |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/webhook/line` | LINE Webhook 接收端點 | LINE Signature | V1.0 |
| GET | `/health` | 健康檢查 | 無 | V1.0 |
| GET | `/metrics` | Prometheus 指標 | 無 (internal) | V1.0 |
| POST | `/auth/login` | 管理員/技師登入 | 無 | V1.0 |
| POST | `/auth/refresh` | 刷新 JWT Token | JWT | V1.0 |
| GET | `/api/v1/cases` | 案例列表查詢 | Admin JWT | V1.0 |
| POST | `/api/v1/cases` | 新增案例 | Admin JWT | V1.0 |
| PUT | `/api/v1/cases/{id}` | 更新案例 | Admin JWT | V1.0 |
| DELETE | `/api/v1/cases/{id}` | 刪除案例 | Admin JWT | V1.0 |
| POST | `/api/v1/manuals/upload` | 上傳 PDF 手冊 | Admin JWT | V1.0 |
| GET | `/api/v1/manuals` | 手冊列表 | Admin JWT | V1.0 |
| GET | `/api/v1/sop-drafts` | 待審核 SOP 列表 | Admin JWT | V1.0 |
| POST | `/api/v1/sop-drafts/{id}/approve` | 審核通過 SOP | Admin JWT | V1.0 |
| POST | `/api/v1/sop-drafts/{id}/reject` | 拒絕 SOP | Admin JWT | V1.0 |
| GET | `/api/v1/conversations` | 對話記錄查詢 | Admin JWT | V1.0 |
| GET | `/api/v1/conversations/{id}` | 對話詳情 | Admin JWT | V1.0 |
| GET | `/api/v1/problem-cards` | 問題卡列表 | Admin JWT | V1.0 |
| GET | `/api/v1/stats/dashboard` | 統計儀表板 | Admin JWT | V1.0 |
| GET | `/api/v2/work-orders` | 工單列表 | Admin/Tech JWT | V2.0 |
| POST | `/api/v2/work-orders` | 建立工單 | Admin JWT | V2.0 |
| PUT | `/api/v2/work-orders/{id}/accept` | 技師接單 | Tech JWT | V2.0 |
| PUT | `/api/v2/work-orders/{id}/reject` | 技師拒單 | Tech JWT | V2.0 |
| PUT | `/api/v2/work-orders/{id}/start` | 開始服務 | Tech JWT | V2.0 |
| PUT | `/api/v2/work-orders/{id}/complete` | 完成服務 | Tech JWT | V2.0 |
| GET | `/api/v2/technicians` | 技師列表 | Admin JWT | V2.0 |
| POST | `/api/v2/technicians` | 新增技師 | Admin JWT | V2.0 |
| GET | `/api/v2/price-rules` | 計價規則列表 | Admin JWT | V2.0 |
| POST | `/api/v2/price-rules` | 新增計價規則 | Admin JWT | V2.0 |
| GET | `/api/v2/invoices` | 發票列表 | Admin JWT | V2.0 |
| GET | `/api/v2/reports/monthly` | 月度統計報表 | Admin JWT | V2.0 |

### 附錄 C：環境變數清單

| 變數名稱 | 說明 | 範例值 | 必填 |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL 連線字串 | `postgresql+asyncpg://user:pass@postgres:5432/smartlock` | 是 |
| `REDIS_URL` | Redis 連線字串 | `redis://redis:6379/0` | 是 |
| `OPENAI_API_KEY` | OpenAI API 金鑰 | `sk-...` | 是 |
| `OPENAI_MODEL` | LLM 模型名稱 | `gpt-4o` | 是 |
| `OPENAI_EMBEDDING_MODEL` | Embedding 模型名稱 | `text-embedding-3-small` | 是 |
| `LINE_CHANNEL_SECRET` | LINE Channel Secret | `abc123...` | 是 |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Channel Access Token | `xyz789...` | 是 |
| `JWT_SECRET` | JWT 簽名密鑰 | `super-secret-key` | 是 |
| `JWT_EXPIRY_HOURS` | JWT 過期時間（小時） | `4` | 否（預設 4） |
| `LOG_LEVEL` | 日誌等級 | `INFO` | 否（預設 INFO） |
| `CORS_ORIGINS` | 允許的 CORS 來源 | `http://localhost:3000` | 否 |
| `VECTOR_SIMILARITY_THRESHOLD` | L1 向量搜尋命中閾值 | `0.85` | 否（預設 0.85） |
| `SESSION_TTL_SECONDS` | 對話 Session 超時（秒） | `1800` | 否（預設 1800） |
| `MAX_CONVERSATION_TURNS` | 最大對話輪數 | `20` | 否（預設 20） |
| `ENVIRONMENT` | 環境標識 | `development` / `staging` / `production` | 否（預設 development） |

### 附錄 D：靜態結構分析參考

- **檔案依賴關係:** 參考 `docs/09_file_dependencies.md`（待產出）
- **類別關係圖:** 參考 `docs/10_class_relationships.md`（待產出）

---

**文件審核記錄 (Review History):**

| 日期 | 審核人 | 版本 | 變更摘要 |
| :--- | :--- | :--- | :--- |
| 2026-02-17 | 技術架構師 | v1.0 | 初稿完成，涵蓋 V1.0 + V2.0 完整架構設計 |
