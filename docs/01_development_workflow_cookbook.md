# 開發流程總覽手冊 (Development Workflow Cookbook)

# 電子鎖智能客服與派工平台 — SmartLock-SaaS

---

**文件版本 (Document Version):** `v1.0`
**最後更新 (Last Updated):** `2026-03-13`
**主要作者 (Lead Author):** `開發團隊`
**狀態 (Status):** `活躍 (Active)`

---

## 目錄 (Table of Contents)

- [Ⅰ. 核心理念：從商業價值到高品質程式碼](#ⅰ-核心理念從商業價值到高品質程式碼)
- [Ⅱ. 開發階段與文件產出](#ⅱ-開發階段與文件產出)
  - [第一階段：規劃 (Planning) - 定義「為何」與「什麼」](#第一階段規劃-planning---定義為何與什麼)
  - [第二階段：設計 (Design) - 定義「如何」的藍圖](#第二階段設計-design---定義如何的藍圖)
  - [第三階段：開發 (Development) - 精確實現](#第三階段開發-development---精確實現)
  - [第四階段：品質與部署 (Quality & Deployment)](#第四階段品質與部署-quality--deployment)
- [Ⅲ. 支援文件](#ⅲ-支援文件)
- [Ⅳ. 文件成熟度總覽](#ⅳ-文件成熟度總覽)

---

## Ⅰ. 核心理念：從商業價值到高品質程式碼

**目的**: 本手冊旨在提供一個頂層指導，說明整個開發流程的各個階段、目標，並作為導航中心，連結到所有相關的文件範本。

本開發流程旨在建立一個從商業需求到高品質程式碼的完整、可追溯的鏈路。我們融合 BDD (行為驅動開發)、DDD (領域驅動設計)、Clean Architecture (潔淨架構) 與 TDD (測試驅動開發)，形成一套以「規格」為驅動、以「測試」為驗證的現代軟體開發模型。

**推演的第一性原理:**

1.  **從「為何」到「什麼」，再到「如何」**:
    *   **為何 (Why)**: 革新電子鎖售後服務，將資深技師的專家知識系統化、可傳承，消除從報修到結案的所有人工瓶頸。
    *   **什麼 (What)**: V1.0 AI 智能客服系統（LINE Bot + ProblemCard + 三層解決引擎 + 自進化知識庫），V2.0 技師派工與帳務平台（智慧媒合派工 + 計價引擎 + 帳務系統）。
    *   **如何 (How)**: FastAPI + PostgreSQL/pgvector + LangChain/Gemini 3 Pro + LINE Bot SDK，以 Clean Architecture + DDD 分層實現。

2.  **品質內建 (Quality Built-in)**: 我們不將測試視為事後檢查，而是將其融入開發的每一步。BDD 情境定義允收標準、模組規格定義函式契約、TDD 確保每一行程式碼都被測試覆蓋，從根本上減少錯誤。

3.  **AI 輔助就緒 (AI-Assistant Ready)**: 流程中的每一份文件都旨在產生精確、無歧義的「上下文」，為大型語言模型 (LLM) 輔助開發提供必要的「護欄」。

---

## Ⅱ. 開發階段與文件產出

本流程分為四個主要階段，每個階段都會產出關鍵文件，環環相扣，共同構成專案的完整藍圖。

### **第一階段：規劃 (Planning) - 定義「為何」與「什麼」**

**目標**: 確保開發方向從一開始就與商業價值和使用者需求對齊。

1.  **[專案簡報與產品需求 (PRD)](./02_project_brief_and_prd.md)** `已批准 (Approved)`
    *   **目的**: 定義專案的「為何」與「為誰」，設定最高層次的目標和邊界。
    *   **產出**: 完整的 PRD 文件，包含商業目標（4 大 KPI：AI 自助解決率 ≥ 60%、首次回應時間 < 5 秒、知識庫每月自動新增 ≥ 10 條 SOP、派工接單率 ≥ 90%）、31 條使用者故事（US-001 ~ US-031）、成功指標及範圍限制。
    *   **關鍵產物**: 五類利害關係人定義（甲方、乙方、消費者、技師、總部管理員）、V1.0/V2.0 交付時程（W1-W17 / W18-W31）。

2.  **[行為驅動情境 (BDD Scenarios)](./03_behavior_driven_development.md)** `活躍 (Active)`
    *   **目的**: 將 PRD 中的使用者故事轉化為精確、無歧義的 Gherkin 規格，作為連接業務與技術的橋樑。
    *   **產出**: 完整的 BDD Feature 文件，涵蓋 V1.0 六大 Feature（LINE Bot 客服對話、ProblemCard 分診、三層解決引擎、自進化知識庫、管理後台、安全防護）與 V2.0 六大 Feature（師傅工作台、智慧派工引擎、標準化定價引擎、自動化會計系統、管理後台 V2.0、V1↔V2 資料串接）。
    *   **通用語言 (Ubiquitous Language)**: ProblemCard（問題卡）、Three-Layer Resolution Engine（三層解決引擎）、SOP Draft（SOP 草稿）、Pricing Engine（定價引擎）、Dispatch Matching（派工匹配）、Case Pool（案件池）、Completion Report（完工回報）。

### **第二階段：設計 (Design) - 定義「如何」的藍圖**

**目標**: 將業務需求轉化為穩固、可擴展的技術藍圖，避免系統演變成難以維護的「大泥球」。

3.  **[架構與設計文檔 (SAD & SDD)](./05_architecture_and_design_document.md)** `已批准 (Approved)`
    *   **目的**: 建立系統的結構（架構）並填充具體的實現細節（設計）。
    *   **產出**: 整合性設計文檔，包含：
        *   **C4 模型**: L1 系統情境圖、L2 容器圖、L3 組件圖（四大組件：LINE Bot Gateway、AI Service Layer、Admin API、Data Layer）
        *   **DDD 戰略設計**: 六大 Bounded Context（conversation、problem_card、knowledge_base、dispatch、pricing、accounting）
        *   **Clean Architecture 分層**: 六層堆疊（UI → API Gateway → AI Service → Business Domain → Data Access → Infrastructure）
        *   **數據架構**: PostgreSQL Schema（`sql/Schema.sql`）、pgvector HNSW 索引策略（768 維、m=16、ef_construction=64）
        *   **部署架構**: 三環境策略（Dev / Staging / Production）、Docker Compose 容器編排
    *   **連結子文件**:
        *   **[架構決策記錄 (ADR)](./adrs/)**: 5 份已決策 ADR
            - ADR-001: 後端框架選型 → FastAPI
            - ADR-002: 資料庫選型 → PostgreSQL 16 + pgvector 0.7
            - ADR-003: LLM 整合框架 → LangChain 0.3 + Google Gemini 3 Pro
            - ADR-004: LINE Bot 架構 → line-bot-sdk-python 3 + Webhook
            - ADR-005: 前端框架選型 (V2.0) → Next.js 14 + shadcn/ui
        *   **[API 設計規格](./06_api_design_specification.md)** `已批准 (Approved)`: RESTful API 全端點規範，涵蓋 V1.0（認證、Webhook、對話、ProblemCard、案例庫、手冊管理、SOP 管理、儀表板）及 V2.0（派工、技師、報價、帳務）端點，含完整的 Request/Response Schema 定義。

4.  **[資料庫 Schema](../sql/Schema.sql)** `已定義 (Defined)`
    *   **目的**: 定義系統的完整數據模型。
    *   **產出**: PostgreSQL DDL，包含 V1.0 核心 8 張表（users、conversations、messages、problem_cards、manuals、manual_chunks、case_entries、sop_drafts）與 V2.0 擴充 6 張表（technicians、work_orders、price_rules、invoices、reconciliations、settlements），含完整索引策略與向量索引。

### **第三階段：開發 (Development) - 精確實現**

**目標**: 透過 TDD 和契約式設計，確保每一個程式碼單元都被精確、健壯地實現。

5.  **[模組規格與測試](./07_module_specification_and_tests.md)** `草稿 (Draft)`
    *   **目的**: 將高層次的 BDD 情境分解到具體的模組或類別層級，並使用契約式設計 (DbC) 來精確定義其職責邊界。
    *   **產出**: V1.0 五大核心模組規格，每個模組包含函式簽名、前置/後置條件、不變式、測試情境：
        - **模組 1: ConversationManager** — 對話編排器，處理意圖辨識、NER、狀態機轉換
        - **模組 2: ProblemCardEngine** — 問題卡生成與完整度評估
        - **模組 3: ThreeLayerResolver** — 三層解決引擎（L1 案例庫 → L2 RAG → L3 轉人工）
        - **模組 4: KnowledgeBaseManager** — 案例庫搜尋與手冊匯入 Pipeline
        - **模組 5: SOPGenerator** — SOP 自動生成與去重

6.  **[模組依賴關係分析](./09_file_dependencies.md)** `草稿 (Draft)`
    *   **目的**: 定義模組間的依賴方向與層級關係，確保依賴方向符合 Clean Architecture 原則（依賴朝內、永不反轉）。
    *   **產出**: 高層級模組依賴圖、關鍵依賴路徑分析、外部依賴管理策略。

7.  **[類別/組件關係文檔](./10_class_relationships.md)** `草稿 (Draft)`
    *   **目的**: 細化領域實體、值物件、聚合根之間的關係。
    *   **產出**: 領域模型類別圖，涵蓋 DDD 六大 Bounded Context 的實體關係。

### **第四階段：品質與部署 (Quality & Deployment)**

**目標**: 確保專案在交付前符合安全、隱私與生產環境的標準。

8.  **[綜合品質檢查清單](./13_security_and_readiness_checklists.md)** `使用中 (In Use)`
    *   **目的**: 在設計階段與部署前進行全面的安全、隱私和生產準備就緒審查。
    *   **產出**: 已完成的檢查清單，涵蓋七大領域：
        - A. 核心安全原則（最小權限、縱深防禦）
        - B. 數據生命週期安全與隱私
        - C. 應用程式安全（OWASP Top 10 對照）
        - D. 基礎設施與運維安全
        - E. 合規性
        - F. 審查結論與行動項
        - G. 生產準備就緒（可觀測性、可靠性、性能、可維護性）

9.  **[部署與運維指南](./14_deployment_and_operations_guide.md)** `草稿 (Draft)`
    *   **目的**: 提供從開發到上線的完整部署操作手冊。
    *   **產出**: 部署架構總覽（三環境策略、Docker Compose 拓撲）、CI/CD 流水線（`ci.yml` + `deploy.yml`）、部署檢查清單。

10. **[Code Review 與重構指南](./11_code_review_and_refactoring_guide.md)** `草稿 (Draft)`
    *   **目的**: 建立團隊統一的 Code Review 標準與重構模式。
    *   **產出**: Review Checklist、常見重構模式、品質閘門定義。

---

## Ⅲ. 支援文件

以下文件不屬於特定階段，但在整個開發生命週期中提供持續支援：

*   **[專案結構指南](./08_project_structure_guide.md)** `活躍 (Active)`: 標準化的 Clean Architecture 目錄結構規範（按領域/功能組織，非按技術類型），確保 V1.0 → V2.0 平滑過渡。
*   **[前端架構規範](./12_frontend_architecture_specification.md)** `草稿 (Draft)`: V2.0 Next.js 14 + shadcn/ui 前端開發規範。
*   **[前端信息架構](./17_frontend_information_architecture.md)** `草稿 (Draft)`: 前端頁面導航、用戶流程、信息層級設計。
*   **[文檔與維護指南](./15_documentation_and_maintenance_guide.md)** `草稿 (Draft)`: 文檔標準與維護流程定義。
*   **[系統架構總覽](./executive_architecture_overview.md)** `已完成 (Completed)`: 高階系統分層堆疊圖與資料流總覽，適用於利害關係人簡報。
*   **[WBS 開發計畫](./WBS_電子鎖智能平台.md)** `已定義 (Defined)`: 31 週工作分解結構，含 8 個 Phase、各工作包的交付物與負責方。
*   **[領域知識資料](../data/)**:
    - `data/RAG/` — RAG 知識庫原始資料
    - `data/transcript/` — 領域專家訪談逐字稿（產品知識、故障排除、系統需求討論）

---

## Ⅳ. 文件成熟度總覽

| 階段 | 文件 | 狀態 | 文件路徑 |
|:-----|:-----|:-----|:---------|
| **規劃** | 專案簡報與 PRD | ✅ 已批准 | `docs/02_project_brief_and_prd.md` |
| **規劃** | BDD 情境 | ✅ 活躍 | `docs/03_behavior_driven_development.md` |
| **設計** | 架構與設計文檔 | ✅ 已批准 | `docs/05_architecture_and_design_document.md` |
| **設計** | ADR (5 份) | ✅ 已決策 | `docs/adrs/adr-001 ~ adr-005` |
| **設計** | API 設計規格 | ✅ 已批准 | `docs/06_api_design_specification.md` |
| **設計** | 資料庫 Schema | ✅ 已定義 | `sql/Schema.sql` |
| **開發** | 模組規格與測試 | 📝 草稿 | `docs/07_module_specification_and_tests.md` |
| **開發** | 模組依賴關係 | 📝 草稿 | `docs/09_file_dependencies.md` |
| **開發** | 類別關係文檔 | 📝 草稿 | `docs/10_class_relationships.md` |
| **品質** | 品質檢查清單 | ✅ 使用中 | `docs/13_security_and_readiness_checklists.md` |
| **品質** | 部署與運維指南 | 📝 草稿 | `docs/14_deployment_and_operations_guide.md` |
| **品質** | Code Review 指南 | 📝 草稿 | `docs/11_code_review_and_refactoring_guide.md` |
| **支援** | 專案結構指南 | ✅ 活躍 | `docs/08_project_structure_guide.md` |
| **支援** | 前端架構規範 | 📝 草稿 | `docs/12_frontend_architecture_specification.md` |
| **支援** | 前端信息架構 | 📝 草稿 | `docs/17_frontend_information_architecture.md` |
| **支援** | 文檔與維護指南 | 📝 草稿 | `docs/15_documentation_and_maintenance_guide.md` |
| **支援** | 系統架構總覽 | ✅ 已完成 | `docs/executive_architecture_overview.md` |
| **支援** | WBS 開發計畫 | ✅ 已定義 | `docs/WBS_電子鎖智能平台.md` |

**當前進度**: Phase 0（需求定義與架構設計）已完成。所有規劃與設計階段的核心文件均已批准，開發階段的模組規格為草稿狀態，專案已就緒進入 Phase 1（AI 客服 MVP 開發）。
