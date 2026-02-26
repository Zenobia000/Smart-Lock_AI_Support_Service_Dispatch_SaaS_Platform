# 模組規格與測試案例 (Module Specification & Test Cases)

# 電子鎖智能客服與派工平台 - V1.0 核心模組

---

**文件版本 (Document Version):** `v1.0`
**最後更新 (Last Updated):** `2026-02-25`
**主要作者 (Lead Author):** `開發工程師`
**審核者 (Reviewers):** `技術負責人`
**狀態 (Status):** `草稿 (Draft)`

---

## 目錄 (Table of Contents)

- [模組 1: ConversationManager (ProcessMessageUseCase)](#模組-1-conversationmanager-processmessageusecase)
  - [規格 1-1: process_message](#規格-1-1-process_message)
  - [規格 1-2: resume_expired_session](#規格-1-2-resume_expired_session)
  - [測試情境與案例](#測試情境與案例-conversationmanager)
- [模組 2: ProblemCardEngine (GenerateProblemCardUseCase)](#模組-2-problemcardengine-generateproblemcardusecase)
  - [規格 2-1: generate_problem_card](#規格-2-1-generate_problem_card)
  - [規格 2-2: evaluate_completeness](#規格-2-2-evaluate_completeness)
  - [測試情境與案例](#測試情境與案例-problemcardengine)
- [模組 3: ThreeLayerResolver (ResolveQueryUseCase)](#模組-3-threelayerresolver-resolvequeryusecase)
  - [規格 3-1: resolve](#規格-3-1-resolve)
  - [規格 3-2: CaseLibraryStrategy.search](#規格-3-2-caselibrarystrategy-search)
  - [規格 3-3: RAGStrategy.generate](#規格-3-3-ragstrategy-generate)
  - [規格 3-4: HumanHandoffStrategy.escalate](#規格-3-4-humanhandoffstrategy-escalate)
  - [測試情境與案例](#測試情境與案例-threelayerresolver)
- [模組 4: KnowledgeBaseManager (SearchCaseLibraryUseCase / IngestManualUseCase)](#模組-4-knowledgebasemanager)
  - [規格 4-1: search_case_library](#規格-4-1-search_case_library)
  - [規格 4-2: ingest_manual](#規格-4-2-ingest_manual)
  - [測試情境與案例](#測試情境與案例-knowledgebasemanager)
- [模組 5: SOPGenerator (DraftSOPUseCase)](#模組-5-sopgenerator-draftsopusecase)
  - [規格 5-1: draft_sop](#規格-5-1-draft_sop)
  - [規格 5-2: check_duplicate](#規格-5-2-check_duplicate)
  - [測試情境與案例](#測試情境與案例-sopgenerator)

---

**目的**: 本文件旨在將高層次的 BDD 情境 (`docs/03_behavior_driven_development.md`) 分解到具體的模組或類別層級，定義其詳細規格、測試場景，並使用契約式設計 (Design by Contract, DbC) 來精確定義每個函式的職責邊界。這是最低層級、最精確的規格，直接指導 TDD (測試驅動開發) 的實踐。

**對應架構文件**: `docs/05_architecture_and_design_document.md`
**對應專案結構**: `docs/08_project_structure_guide.md`
**對應資料庫 Schema**: `SQL/Schema.sql`

---

## 模組 1: ConversationManager (ProcessMessageUseCase)

**所在路徑**: `backend/src/smart_lock/application/conversation/use_cases.py`
**對應領域層**: `backend/src/smart_lock/domains/conversation/entities.py`
**對應 BDD Feature**: `docs/03_behavior_driven_development.md#feature-line-bot-ai-客服對話`
**對應 API 端點**: `POST /api/v1/webhook/line` (LINE Webhook Handler 內部呼叫)

**模組描述**: ConversationManager 是 LINE Bot 客服對話的核心編排器。負責接收使用者訊息後，執行意圖辨識、NER 實體擷取、對話狀態機轉換、ProblemCard 更新，並在資訊收集完成後觸發三層解決引擎。此模組必須在 LINE Webhook 的 1 秒回應限制下，將 LLM 呼叫 (2-10 秒) 委派至非同步任務處理。

---

### 規格 1-1: `process_message`

**描述 (Description)**: 接收一則來自 LINE 使用者的訊息，根據當前對話狀態執行相應的業務邏輯（意圖辨識、資訊擷取、狀態轉換），並產生 AI 回覆訊息。

**函式簽名**:
```python
async def process_message(
    self,
    line_user_id: str,
    message_content: str,
    content_type: str = "text",
    metadata: dict | None = None,
) -> ConversationResponseDTO:
```

**契約式設計 (Design by Contract, DbC)**:

*   **前置條件 (Preconditions)**:
    1. `line_user_id` 不可為空，且格式必須為 `U` + 32 位十六進位字元（共 33 字元）。
    2. `message_content` 不可為空字串（text 類型時）。
    3. `content_type` 必須為 `"text"`, `"image"`, `"location"` 之一。
    4. LINE Webhook 簽章驗證已通過（由上層 Webhook Controller 確保）。
    5. Redis 連線可用（用於讀寫對話 Session Cache）。

*   **後置條件 (Postconditions)**:
    1. 使用者訊息已持久化至 `messages` 表，`role` 為 `"user"`。
    2. AI 回覆訊息已持久化至 `messages` 表，`role` 為 `"assistant"`。
    3. 所屬 `conversations` 記錄的 `message_count` 已遞增。
    4. 對話上下文 (`conversations.context` JSONB) 已根據本輪對話更新（包含 `intent`, `collected_fields`, `missing_fields`, `turn_count`）。
    5. 若為新使用者首次訊息，則 `users` 表已建立對應記錄（呼叫 LINE Get Profile API 取得 `display_name`）。
    6. 若為新對話，則 `conversations` 表已建立新記錄，`status` 為 `"active"`，Redis Session Cache 已寫入。
    7. 回傳的 `ConversationResponseDTO` 包含 `reply_messages`（至少一則）與 `conversation_id`。
    8. 整個方法的同步部分（排除 LLM 呼叫）在 500ms 以內完成，LLM 呼叫透過 `asyncio.create_task` 非同步執行。

*   **不變性 (Invariants)**:
    1. 一個 `conversations` 記錄最多關聯一張 `problem_cards` 記錄（1:1 UNIQUE FK）。
    2. 對話狀態只能依照狀態機規則轉換：`active -> collecting -> resolving -> resolved | escalated`，或 `active | collecting -> expired`。
    3. `conversations.message_count` 永遠等於其關聯的 `messages` 記錄總數。
    4. `users.last_active_at` 在每次互動後更新。

---

### 規格 1-2: `resume_expired_session`

**描述 (Description)**: 當使用者在對話超時（30 分鐘無互動）後發送新訊息時，恢復之前的對話上下文，從中斷處繼續收集資訊。

**函式簽名**:
```python
async def resume_expired_session(
    self,
    line_user_id: str,
    expired_conversation_id: uuid.UUID,
) -> ConversationResponseDTO:
```

**契約式設計 (Design by Contract, DbC)**:

*   **前置條件 (Preconditions)**:
    1. `expired_conversation_id` 對應的 `conversations` 記錄存在且 `status` 為 `"expired"`。
    2. 該對話的 `context` JSONB 中包含可恢復的上下文資料（`collected_fields` 不為空）。
    3. `line_user_id` 對應的使用者為該對話的擁有者（`conversations.user_id` 匹配）。

*   **後置條件 (Postconditions)**:
    1. 建立一個新的 `conversations` 記錄，`status` 為 `"collecting"`。
    2. 新對話的 `context` JSONB 從舊對話中繼承 `collected_fields`，`missing_fields` 重新計算。
    3. AI 回覆訊息包含之前已收集的資訊摘要，並詢問下一個缺失欄位。
    4. 舊對話記錄維持 `status = "expired"` 不變。

*   **不變性 (Invariants)**:
    1. 已收集的 ProblemCard 欄位資料不因超時而遺失。
    2. 新對話必須建立新的 `session_id` 並寫入 Redis。

---

### 測試情境與案例 (ConversationManager)

#### 情境 1: 正常路徑 — 新使用者首次發送問題訊息

*   **測試案例 ID**: `TC-CM-001`
*   **描述**: 一個從未互動過的 LINE 使用者發送第一則訊息，系統應建立使用者、建立對話、辨識意圖，並回覆問候語。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - Mock `LINE Get Profile API` 回傳 `{"displayName": "王小明", "pictureUrl": "https://..."}`。
        - Mock `LLMGateway.classify_intent()` 回傳 `"lock_malfunction"`。
        - 資料庫中無 `line_user_id = "Uabc123...def"` 的使用者記錄。
    2.  **Act**: 呼叫 `process_message(line_user_id="Uabc123...def", message_content="我家的電子鎖打不開")`。
    3.  **Assert**:
        - 驗證 `users` 表新增一筆記錄，`display_name` 為 `"王小明"`，`role` 為 `"line_user"`。
        - 驗證 `conversations` 表新增一筆記錄，`status` 為 `"collecting"`。
        - 驗證 `messages` 表新增兩筆記錄（user + assistant）。
        - 驗證回傳的 `ConversationResponseDTO.reply_messages` 包含問候語且詢問品牌資訊。
        - 驗證 `conversations.context` 包含 `{"intent": "lock_malfunction", "collected_fields": {}, "missing_fields": ["brand", "model", "location", "door_status", "symptoms"]}`。

#### 情境 2: 正常路徑 — 多輪對話逐步收集 ProblemCard 資訊

*   **測試案例 ID**: `TC-CM-002`
*   **描述**: 使用者在已有的對話中回答品牌問題，系統應更新對話上下文中的 `collected_fields`。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - 已存在 `conversations` 記錄，`status = "collecting"`，`context = {"intent": "lock_malfunction", "collected_fields": {}, "missing_fields": ["brand", "model", "location", "door_status", "symptoms"]}`。
        - Mock `LLMGateway.extract_entities()` 回傳 `{"brand": "Yale"}`。
    2.  **Act**: 呼叫 `process_message(line_user_id="Uabc123...def", message_content="品牌是 Yale")`。
    3.  **Assert**:
        - 驗證 `conversations.context.collected_fields` 更新為 `{"brand": "Yale"}`。
        - 驗證 `conversations.context.missing_fields` 不再包含 `"brand"`。
        - 驗證回覆訊息詢問下一個缺失欄位（型號）。
        - 驗證 `conversations.message_count` 遞增 2。

#### 情境 3: 正常路徑 — 資訊收集完成觸發三層解決引擎

*   **測試案例 ID**: `TC-CM-003`
*   **描述**: 使用者提供最後一個缺失欄位後，系統應將對話狀態轉為 `"resolving"` 並觸發 ThreeLayerResolver。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - 已存在 `conversations` 記錄，`status = "collecting"`，`context.collected_fields = {"brand": "Yale", "model": "YDM-7116", "location": "台北市信義區", "door_status": "closed_locked"}`，`context.missing_fields = ["symptoms"]`。
        - Mock `LLMGateway.extract_entities()` 回傳 `{"symptoms": "密碼鍵盤完全沒反應"}`。
        - Mock `ProblemCardEngine.generate_problem_card()` 回傳 ProblemCard with `status = "confirmed"`。
        - Mock `ThreeLayerResolver.resolve()` 回傳 `ResolutionResultDTO` with `resolution_layer = "L1"`。
    2.  **Act**: 呼叫 `process_message(line_user_id="Uabc123...def", message_content="密碼鍵盤完全沒反應，沒有燈光")`。
    3.  **Assert**:
        - 驗證 `conversations.status` 轉為 `"resolving"`，最終轉為 `"resolved"`。
        - 驗證 `problem_cards` 表已建立記錄，所有欄位填充完整。
        - 驗證 `ThreeLayerResolver.resolve()` 被呼叫。
        - 驗證回覆訊息包含解決方案內容。

#### 情境 4: 邊界情況 — 對話超時後恢復

*   **測試案例 ID**: `TC-CM-004`
*   **描述**: 使用者在對話超時（30 分鐘）後發送新訊息，系統應恢復先前的對話上下文。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - 已存在 `conversations` 記錄，`status = "expired"`，`context.collected_fields = {"brand": "Gateman"}`。
        - 該使用者無其他 `active` 狀態的對話。
    2.  **Act**: 呼叫 `process_message(line_user_id="Uabc123...def", message_content="抱歉剛剛在忙")`。
    3.  **Assert**:
        - 驗證新建一筆 `conversations` 記錄，`status = "collecting"`。
        - 驗證新對話的 `context.collected_fields` 包含 `{"brand": "Gateman"}`。
        - 驗證回覆訊息包含 `"Gateman"` 品牌名稱，並詢問型號。

#### 情境 5: 無效輸入 — 使用者發送不相關訊息

*   **測試案例 ID**: `TC-CM-005`
*   **描述**: 使用者發送與電子鎖無關的訊息，系統應禮貌性導引回電子鎖問題。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - 已存在 `conversations` 記錄，`status = "active"`。
        - Mock `LLMGateway.classify_intent()` 回傳 `"off_topic"`。
    2.  **Act**: 呼叫 `process_message(line_user_id="Uabc123...def", message_content="今天天氣不錯")`。
    3.  **Assert**:
        - 驗證 `conversations.status` 維持 `"active"` 不變（不進入 `"collecting"`）。
        - 驗證回覆訊息包含引導語，例如 `"我是電子鎖客服助手，請問您的電子鎖有什麼問題需要協助嗎？"`。
        - 驗證未建立 `problem_cards` 記錄。

#### 情境 6: 無效輸入 — LINE User ID 格式不合法

*   **測試案例 ID**: `TC-CM-006`
*   **描述**: 傳入格式不合法的 `line_user_id`，系統應拋出驗證例外。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**: 無特殊前置。
    2.  **Act**: 呼叫 `process_message(line_user_id="invalid_id", message_content="test")`。
    3.  **Assert**:
        - 預期系統拋出 `ValidationError`，錯誤訊息包含 `"line_user_id"`。
        - 驗證資料庫未寫入任何記錄。

#### 情境 7: 業務規則 — LINE Webhook 非同步處理保證 1 秒內回應

*   **測試案例 ID**: `TC-CM-007`
*   **描述**: LLM 呼叫耗時 5 秒時，Webhook Handler 仍應在 1 秒內回傳 HTTP 200，LLM 結果透過非同步推播。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - Mock `LLMGateway` 所有方法延遲 5 秒回傳。
        - 設定計時器追蹤 `process_message` 的同步回傳時間。
    2.  **Act**: 呼叫 `process_message(line_user_id="Uabc123...def", message_content="電子鎖打不開")`。
    3.  **Assert**:
        - 驗證方法的同步部分在 1000ms 以內回傳。
        - 驗證 LLM 呼叫已透過 `asyncio.create_task` 排入非同步佇列。
        - 驗證回傳的 DTO 包含 `processing = True` 標記（表示正在非同步處理）。

#### 情境 8: 業務規則 — 同一使用者並行對話限制

*   **測試案例 ID**: `TC-CM-008`
*   **描述**: 同一使用者不應同時擁有多個 `active` 或 `collecting` 狀態的對話。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - 已存在 `conversations` 記錄，`status = "collecting"`，屬於使用者 `"Uabc123...def"`。
    2.  **Act**: 使用者發送新訊息，系統嘗試處理。
    3.  **Assert**:
        - 驗證系統不會建立新的 `conversations` 記錄。
        - 驗證訊息加入到既有的進行中對話。

---

## 模組 2: ProblemCardEngine (GenerateProblemCardUseCase)

**所在路徑**: `backend/src/smart_lock/application/problem_card/use_cases.py`
**對應領域層**: `backend/src/smart_lock/domains/problem_card/entities.py`
**對應 BDD Feature**: `docs/03_behavior_driven_development.md#feature-problemcard-智慧分診`
**對應資料庫表**: `problem_cards`

**模組描述**: ProblemCardEngine 負責從多輪對話中萃取結構化資訊，生成 ProblemCard 診斷卡。它使用 LLM 進行實體擷取（品牌、型號、位置、門況、網路狀態、症狀），計算欄位完整度分數，並在資訊不足時產生追問問題。ProblemCard 是三層解決引擎的核心輸入。

---

### 規格 2-1: `generate_problem_card`

**描述 (Description)**: 從對話上下文與訊息記錄中，利用 LLM 提取結構化欄位，建立或更新 ProblemCard。

**函式簽名**:
```python
async def generate_problem_card(
    self,
    conversation_id: uuid.UUID,
    collected_fields: dict,
    conversation_messages: list[MessageDTO],
) -> ProblemCardResponseDTO:
```

**契約式設計 (Design by Contract, DbC)**:

*   **前置條件 (Preconditions)**:
    1. `conversation_id` 對應的 `conversations` 記錄必須存在。
    2. `collected_fields` 為字典，鍵為 ProblemCard 欄位名稱（`brand`, `model`, `location`, `door_status`, `network_status`, `symptoms`），值為字串或 null。
    3. `conversation_messages` 至少包含一則 `role = "user"` 的訊息。
    4. LLMGateway 服務可用。

*   **後置條件 (Postconditions)**:
    1. `problem_cards` 表中已建立或更新一筆記錄，`conversation_id` 外鍵指向傳入的對話。
    2. `completeness_score` 已根據關鍵欄位填充率重新計算（計算公式見規格 2-2）。
    3. `extracted_fields` JSONB 中記錄了 LLM 每個欄位的原始擷取結果與 confidence score。
    4. 若 `completeness_score >= 0.6`（至少 `brand` + `symptoms` 已填），`status` 為 `"confirmed"` 或保持 `"incomplete"`（視是否有使用者確認）。
    5. 回傳的 `ProblemCardResponseDTO` 包含 `missing_fields` 列表與對應的 `follow_up_questions`。

*   **不變性 (Invariants)**:
    1. `completeness_score` 永遠在 `0.0` ~ `1.0` 之間。
    2. 一個 `conversations` 最多對應一張 `problem_cards`（UNIQUE FK 約束）。
    3. `symptoms` JSONB 欄位始終為陣列格式。

---

### 規格 2-2: `evaluate_completeness`

**描述 (Description)**: 根據 ProblemCard 的欄位填充情況計算完整度分數。

**函式簽名**:
```python
def evaluate_completeness(self, problem_card: ProblemCard) -> float:
```

**契約式設計 (Design by Contract, DbC)**:

*   **前置條件 (Preconditions)**:
    1. `problem_card` 為合法的 ProblemCard 實體（非 None）。

*   **後置條件 (Postconditions)**:
    1. 回傳值為 `0.0` ~ `1.0` 之間的浮點數。
    2. 計算規則：`brand` 權重 0.25，`symptoms` 權重 0.25，`model` 權重 0.15，`location` 權重 0.15，`door_status` 權重 0.10，`network_status` 權重 0.10。
    3. 某欄位非空（非 None 且非空字串）時，獲得該權重的全部分數。

*   **不變性 (Invariants)**:
    1. 欄位權重之和始終等於 `1.0`。
    2. 此方法為純函式，不產生副作用。

---

### 測試情境與案例 (ProblemCardEngine)

#### 情境 1: 正常路徑 — 所有欄位齊全時生成完整 ProblemCard

*   **測試案例 ID**: `TC-PCE-001`
*   **描述**: 對話中已收集到全部六個欄位，系統應生成 `completeness_score = 1.0` 的 ProblemCard。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - 建立 `conversation_id` 對應的對話記錄。
        - 設定 `collected_fields = {"brand": "Samsung", "model": "SHP-DP609", "location": "新北市板橋區", "door_status": "closed_locked", "network_status": "wifi_connected", "symptoms": "指紋辨識失敗率突然升高"}`。
        - Mock LLMGateway 回傳與 `collected_fields` 一致的擷取結果。
    2.  **Act**: 呼叫 `generate_problem_card(conversation_id, collected_fields, messages)`。
    3.  **Assert**:
        - 驗證 `problem_cards` 表中記錄的 `brand` 為 `"Samsung"`、`model` 為 `"SHP-DP609"`。
        - 驗證 `completeness_score` 為 `1.0`。
        - 驗證 `status` 為 `"confirmed"`。
        - 驗證回傳 DTO 的 `missing_fields` 為空列表。

#### 情境 2: 正常路徑 — 僅有品牌與症狀的最低限度 ProblemCard

*   **測試案例 ID**: `TC-PCE-002`
*   **描述**: 僅收集到 `brand` 和 `symptoms`，ProblemCard 達到觸發解決引擎的最低門檻。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - 設定 `collected_fields = {"brand": "Yale", "symptoms": "鎖打不開"}`，其餘欄位為 null。
    2.  **Act**: 呼叫 `generate_problem_card(conversation_id, collected_fields, messages)`。
    3.  **Assert**:
        - 驗證 `completeness_score` 為 `0.5`（brand 0.25 + symptoms 0.25）。
        - 驗證 `missing_fields` 包含 `["model", "location", "door_status", "network_status"]`。
        - 驗證 `follow_up_questions` 非空，第一個問題詢問型號。

#### 情境 3: 邊界情況 — 停產型號處理

*   **測試案例 ID**: `TC-PCE-003`
*   **描述**: 使用者的電子鎖型號已標記為停產，系統應在 ProblemCard 中標記並提供替代建議。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - 設定 `collected_fields = {"brand": "Milre", "model": "MI-6800"}`。
        - 產品資料庫中 `MI-6800` 標記為 `discontinued = true`，替代型號為 `["MI-7800", "MI-8000"]`。
    2.  **Act**: 呼叫 `generate_problem_card(conversation_id, collected_fields, messages)`。
    3.  **Assert**:
        - 驗證 `extracted_fields` JSONB 中包含 `"discontinued_model": true`。
        - 驗證回傳 DTO 包含替代型號建議。
        - 驗證系統仍繼續處理（不因停產而中斷服務）。

#### 情境 4: 邊界情況 — 重複生成 ProblemCard（冪等性）

*   **測試案例 ID**: `TC-PCE-004`
*   **描述**: 同一 `conversation_id` 重複呼叫 `generate_problem_card`，應更新既有記錄而非建立新記錄。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - 已存在 `problem_cards` 記錄，`conversation_id` 對應，`brand = "Yale"`，`model = null`。
        - 新的 `collected_fields = {"brand": "Yale", "model": "YDM-7116"}`。
    2.  **Act**: 呼叫 `generate_problem_card(conversation_id, collected_fields, messages)`。
    3.  **Assert**:
        - 驗證 `problem_cards` 表中仍只有一筆記錄（未重複建立）。
        - 驗證 `model` 已更新為 `"YDM-7116"`。
        - 驗證 `completeness_score` 已重新計算。

#### 情境 5: 無效輸入 — 空的對話訊息列表

*   **測試案例 ID**: `TC-PCE-005`
*   **描述**: 傳入空的 `conversation_messages`，系統應拋出驗證例外。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**: 設定 `conversation_messages = []`。
    2.  **Act**: 呼叫 `generate_problem_card(conversation_id, {}, [])`。
    3.  **Assert**:
        - 預期系統拋出 `ValidationError`，訊息包含 `"conversation_messages"`。
        - 驗證 `problem_cards` 表未寫入任何記錄。

#### 情境 6: 業務規則 — 優先度自動分類

*   **測試案例 ID**: `TC-PCE-006`
*   **描述**: 根據 `door_status` 與 `symptoms` 自動設定 ProblemCard 的 `urgency` 等級。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - 測試案例 A: `door_status = "locked_out"`, `symptoms = "密碼鍵盤無回應"` => 預期 `urgency = "high"`。
        - 測試案例 B: `door_status = "locked_out"`, `symptoms = "人被鎖在門外"` => 預期 `urgency = "urgent"`。
        - 測試案例 C: `door_status = "normal"`, `symptoms = "WiFi 連線失敗"` => 預期 `urgency = "low"`。
    2.  **Act**: 分別呼叫 `generate_problem_card`。
    3.  **Assert**:
        - 驗證各案例的 `urgency` 欄位符合預期分類。

---

## 模組 3: ThreeLayerResolver (ResolveQueryUseCase)

**所在路徑**: `backend/src/smart_lock/application/resolution/use_cases.py`
**對應領域層**: `backend/src/smart_lock/domains/resolution/strategies.py`
**對應 BDD Feature**: `docs/03_behavior_driven_development.md#feature-三層解決引擎`
**對應資料庫表**: `conversations.resolution_layer`, `problem_cards.resolution_layer`

**模組描述**: ThreeLayerResolver 是系統的核心解決引擎，採用策略模式 (Strategy Pattern) 依序嘗試三層解決策略：L1 案例庫向量搜尋（CaseLibraryStrategy） -> L2 PDF 手冊 RAG（RAGStrategy） -> L3 人工轉接（HumanHandoffStrategy）。每一層有明確的信心分數閾值，未達標則自動降級至下一層。

---

### 規格 3-1: `resolve`

**描述 (Description)**: 接收一張已確認的 ProblemCard，依序執行三層解決策略，回傳最終解決結果。

**函式簽名**:
```python
async def resolve(
    self,
    problem_card: ProblemCardResponseDTO,
    conversation_id: uuid.UUID,
) -> ResolutionResultDTO:
```

**契約式設計 (Design by Contract, DbC)**:

*   **前置條件 (Preconditions)**:
    1. `problem_card` 的 `completeness_score >= 0.5`（至少包含 `brand` 與 `symptoms`）。
    2. `problem_card.status` 為 `"confirmed"` 或 `"incomplete"`（至少滿足最低欄位需求）。
    3. `conversation_id` 對應的對話記錄存在且 `status` 為 `"resolving"`。

*   **後置條件 (Postconditions)**:
    1. 回傳的 `ResolutionResultDTO` 必須包含 `resolution_layer`（`"L1"`, `"L2"`, `"L3"` 之一）。
    2. 若 L1 或 L2 解決成功，`answer` 欄位包含解決方案文字，`source_references` 列出引用來源。
    3. 若最終升級至 L3，`needs_escalation = True`，`escalation_info` 包含人工轉接的相關資訊。
    4. `conversations.resolution_layer` 與 `problem_cards.resolution_layer` 已更新為最終解決層級。
    5. 每層嘗試的結果（包含 `layer`, `score`, `success`, `duration_ms`）記錄至日誌。

*   **不變性 (Invariants)**:
    1. 層級嘗試順序永遠為 L1 -> L2 -> L3，不可跳層或倒退。
    2. 若 L1 命中（score >= 0.85），不應再執行 L2 或 L3。
    3. L3 為最終 fallback，必定「成功」（定義為建立人工轉接請求）。

---

### 規格 3-2: CaseLibraryStrategy.search

**描述 (Description)**: L1 策略 — 將 ProblemCard 的問題描述向量化後，對 `case_entries` 表執行 pgvector cosine similarity 搜尋。

**函式簽名**:
```python
async def search(
    self,
    problem_description: str,
    brand: str | None = None,
    model: str | None = None,
    top_k: int = 3,
    threshold: float = 0.85,
) -> list[CaseSearchResultDTO]:
```

**契約式設計 (Design by Contract, DbC)**:

*   **前置條件 (Preconditions)**:
    1. `problem_description` 不可為空字串。
    2. `top_k` 必須大於 0 且小於等於 10。
    3. `threshold` 必須在 `0.0` ~ `1.0` 之間。
    4. Embedding Service（text-embedding-004）可用。
    5. PostgreSQL + pgvector 連線可用。

*   **後置條件 (Postconditions)**:
    1. 回傳的列表長度在 `0` ~ `top_k` 之間。
    2. 列表中每個結果的 `similarity_score` 都 >= `threshold`。
    3. 列表按 `similarity_score` 降序排列。
    4. 每個結果包含 `case_entry_id`, `title`, `solution`, `similarity_score`, `brand`, `lock_type`。
    5. 若提供了 `brand` 和/或 `model`，搜尋結果應優先匹配相同品牌/型號的案例（但不排除其他）。
    6. 命中的 `case_entries` 記錄的 `hit_count` 遞增 1。

*   **不變性 (Invariants)**:
    1. 只搜尋 `is_active = true` 的案例條目。
    2. Embedding 向量維度始終為 768（text-embedding-004）。
    3. 搜尋使用 HNSW 索引（cosine similarity），不使用暴力搜尋。

---

### 規格 3-3: RAGStrategy.generate

**描述 (Description)**: L2 策略 — 基於 ProblemCard 的問題描述，從 `manual_chunks` 檢索相關段落，結合 Gemini 3 Pro 生成解決方案。

**函式簽名**:
```python
async def generate(
    self,
    problem_card: ProblemCardResponseDTO,
    top_k_chunks: int = 5,
    confidence_threshold: float = 0.70,
) -> RAGResultDTO:
```

**契約式設計 (Design by Contract, DbC)**:

*   **前置條件 (Preconditions)**:
    1. `problem_card` 至少包含 `brand` 和 `symptoms` 欄位。
    2. `top_k_chunks` 必須大於 0 且小於等於 20。
    3. `confidence_threshold` 必須在 `0.0` ~ `1.0` 之間。
    4. Embedding Service、LLMGateway（Gemini 3 Pro）、PostgreSQL + pgvector 連線均可用。

*   **後置條件 (Postconditions)**:
    1. 回傳的 `RAGResultDTO` 包含 `answer`（生成的解決方案文字）、`confidence_score`、`source_chunks`（引用的手冊段落列表）。
    2. 若 `confidence_score >= confidence_threshold`，`success = True`。
    3. `source_chunks` 中每個段落包含 `manual_chunk_id`, `source_pdf`, `page_number`, `chapter_title`, `relevance_score`。
    4. 生成的 `answer` 通過 Content Filter 驗證（無幻覺、無有害內容）。
    5. LLM 呼叫的 `token_usage` 與 `latency_ms` 記錄至 `messages.metadata` JSONB。

*   **不變性 (Invariants)**:
    1. RAG 檢索只搜尋 `status = "completed"` 的手冊對應的 `manual_chunks`。
    2. Prompt Template 使用 `configs/prompts/rag_answer.txt`，不可在程式碼中 hardcode。
    3. LLM 回應的 Token 總量不超過設定上限（防止成本失控）。

---

### 規格 3-4: HumanHandoffStrategy.escalate

**描述 (Description)**: L3 策略 — 當 L1 和 L2 均無法解決問題時，建立人工轉接請求，將 ProblemCard 與完整對話記錄轉交客服人員。

**函式簽名**:
```python
async def escalate(
    self,
    problem_card: ProblemCardResponseDTO,
    conversation_id: uuid.UUID,
    reason: str = "auto_escalation",
) -> EscalationResultDTO:
```

**契約式設計 (Design by Contract, DbC)**:

*   **前置條件 (Preconditions)**:
    1. `problem_card` 已存在且有有效的 `id`。
    2. `conversation_id` 對應的對話記錄存在。
    3. `reason` 為合法的升級原因字串（`"auto_escalation"`, `"user_request"`, `"content_filter_triggered"`）。

*   **後置條件 (Postconditions)**:
    1. `conversations.status` 更新為 `"escalated"`。
    2. `problem_cards.status` 更新為 `"escalated"`。
    3. `conversations.resolution_layer` 更新為 `"L3"`。
    4. 回傳的 `EscalationResultDTO` 包含 `ticket_id`（支援工單 ID）或 `work_order_id`（V2.0 派工單 ID）。
    5. 若在服務時間內（09:00-21:00），通知線上客服人員。
    6. 若在服務時間外，建立排程回撥（下一個營業日 09:00），並回傳預計聯繫時間。
    7. 使用者收到的 LINE 訊息包含案件編號與預估等待時間。

*   **不變性 (Invariants)**:
    1. ProblemCard 與完整對話記錄必須附加在轉接請求中。
    2. L3 升級不可失敗（即使無線上客服，也必須建立記錄並排程回撥）。

---

### 測試情境與案例 (ThreeLayerResolver)

#### 情境 1: 正常路徑 — L1 高信心命中直接解決

*   **測試案例 ID**: `TC-TLR-001`
*   **描述**: ProblemCard 的問題在案例庫中有高度匹配的解決方案（similarity >= 0.85），L1 直接解決。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - 建立 ProblemCard: `brand = "Yale"`, `model = "YDM-7116"`, `symptoms = "密碼鍵盤無回應"`。
        - Mock `CaseLibraryStrategy.search()` 回傳 `[{similarity_score: 0.89, solution: "使用 9V 電池緊急供電..."}]`。
    2.  **Act**: 呼叫 `resolve(problem_card, conversation_id)`。
    3.  **Assert**:
        - 驗證回傳 `resolution_layer = "L1"`，`success = True`。
        - 驗證 `answer` 包含解決方案內容。
        - 驗證 `RAGStrategy.generate()` **未被呼叫**。
        - 驗證 `HumanHandoffStrategy.escalate()` **未被呼叫**。
        - 驗證 `conversations.resolution_layer` 更新為 `"L1"`。

#### 情境 2: 正常路徑 — L1 未命中，L2 RAG 成功解決

*   **測試案例 ID**: `TC-TLR-002`
*   **描述**: L1 搜尋結果低於閾值，自動降級至 L2 RAG，RAG 成功生成解決方案。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - 建立 ProblemCard: `brand = "Samsung"`, `model = "SHP-DP609"`, `symptoms = "如何新增臨時密碼給訪客"`。
        - Mock `CaseLibraryStrategy.search()` 回傳空列表（最高 score 0.52，低於 0.85）。
        - Mock `RAGStrategy.generate()` 回傳 `{confidence_score: 0.82, answer: "在室內面板按下設定鍵..."}`。
    2.  **Act**: 呼叫 `resolve(problem_card, conversation_id)`。
    3.  **Assert**:
        - 驗證回傳 `resolution_layer = "L2"`，`success = True`。
        - 驗證 `answer` 包含步驟化解決方案。
        - 驗證 `source_references` 列出引用的手冊段落。
        - 驗證 `HumanHandoffStrategy.escalate()` **未被呼叫**。

#### 情境 3: 正常路徑 — L1 和 L2 均失敗，升級至 L3

*   **測試案例 ID**: `TC-TLR-003`
*   **描述**: L1 和 L2 均無法提供合格的解決方案，系統自動升級至 L3 人工轉接。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - 建立 ProblemCard: `brand = "Gateman"`, `model = "WV-40"`, `symptoms = "鎖舌卡住完全無法轉動"`, `door_status = "locked_out"`, `urgency = "urgent"`。
        - Mock `CaseLibraryStrategy.search()` 回傳空列表（最高 score 0.41）。
        - Mock `RAGStrategy.generate()` 回傳 `{confidence_score: 0.38, success: False}`。
    2.  **Act**: 呼叫 `resolve(problem_card, conversation_id)`。
    3.  **Assert**:
        - 驗證回傳 `resolution_layer = "L3"`，`needs_escalation = True`。
        - 驗證 `escalation_info` 包含 `ticket_id` 與 `priority = "urgent"`。
        - 驗證 `conversations.status` 為 `"escalated"`。

#### 情境 4: 邊界情況 — L1 多個接近閾值的模糊匹配

*   **測試案例 ID**: `TC-TLR-004`
*   **描述**: L1 搜尋回傳多個 similarity score 接近的結果（例如 0.88, 0.86, 0.85），系統應提供候選清單讓使用者選擇。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - 建立 ProblemCard: `brand = "Yale"`, `model = "YDR-323"`, `symptoms = "開門時發出異常聲音"`。
        - Mock `CaseLibraryStrategy.search()` 回傳三筆結果，scores 分別為 0.88, 0.86, 0.85。
    2.  **Act**: 呼叫 `resolve(problem_card, conversation_id)`。
    3.  **Assert**:
        - 驗證回傳 `resolution_layer = "L1"`。
        - 驗證 `answer` 包含三個候選方案，格式為可選擇的列表。
        - 驗證 `requires_user_selection = True`。

#### 情境 5: 邊界情況 — L1 閾值邊界值行為

*   **測試案例 ID**: `TC-TLR-005`
*   **描述**: 測試 similarity score 恰好等於閾值 0.85 的邊界行為。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - Mock `CaseLibraryStrategy.search(threshold=0.85)` 回傳 `[{similarity_score: 0.85, ...}]`。
    2.  **Act**: 呼叫 `resolve(problem_card, conversation_id)`。
    3.  **Assert**:
        - 驗證 `resolution_layer = "L1"` （0.85 **包含在**閾值內，即 `>=` 而非 `>`）。
        - 驗證 `success = True`。

#### 情境 6: 無效輸入 — ProblemCard 未達最低完整度

*   **測試案例 ID**: `TC-TLR-006`
*   **描述**: 傳入 `completeness_score < 0.5` 的 ProblemCard（例如只有 `brand`，缺 `symptoms`），系統應拒絕處理。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - 建立 ProblemCard: `brand = "Yale"`, 其餘所有欄位為 null，`completeness_score = 0.25`。
    2.  **Act**: 呼叫 `resolve(problem_card, conversation_id)`。
    3.  **Assert**:
        - 預期系統拋出 `ValidationError`，訊息包含 `"completeness_score"` 或 `"symptoms"`。
        - 驗證三層策略均未被執行。

#### 情境 7: 業務規則 — L3 非營業時間升級

*   **測試案例 ID**: `TC-TLR-007`
*   **描述**: L3 升級發生在非營業時間（02:30 AM），系統應建立排程回撥而非即時轉接。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - Mock 系統時間為 `02:30 AM`。
        - Mock `CaseLibraryStrategy` 與 `RAGStrategy` 均回傳失敗。
        - Mock 線上客服人員數量為 0。
    2.  **Act**: 呼叫 `resolve(problem_card, conversation_id)`。
    3.  **Assert**:
        - 驗證回傳的 `escalation_info` 包含 `scheduled_callback_at = "09:00"`（次日營業時間）。
        - 驗證 `conversations.status` 為 `"escalated"`，但實際處理時間為排程時間。
        - 驗證回覆訊息包含案件編號與 `"明天上班後第一時間聯繫您"` 語意。

#### 情境 8: 業務規則 — Embedding Service 不可用時的降級處理

*   **測試案例 ID**: `TC-TLR-008`
*   **描述**: Embedding Service 暫時不可用，L1 和 L2 均無法執行向量搜尋，系統應直接降級至 L3。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - Mock `EmbeddingService` 拋出 `ExternalServiceError`。
    2.  **Act**: 呼叫 `resolve(problem_card, conversation_id)`。
    3.  **Assert**:
        - 驗證系統不拋出未捕獲的例外。
        - 驗證回傳 `resolution_layer = "L3"`，`needs_escalation = True`。
        - 驗證日誌中記錄 Embedding Service 失敗的警告。
        - 驗證 `escalation_info.reason` 包含 `"external_service_unavailable"`。

---

## 模組 4: KnowledgeBaseManager

### SearchCaseLibraryUseCase / IngestManualUseCase

**所在路徑**: `backend/src/smart_lock/application/knowledge_base/use_cases.py`
**對應領域層**: `backend/src/smart_lock/domains/knowledge_base/entities.py`
**對應 BDD Feature**: `docs/03_behavior_driven_development.md#feature-自進化知識庫`
**對應資料庫表**: `case_entries`, `manuals`, `manual_chunks`

**模組描述**: KnowledgeBaseManager 負責知識庫的讀寫操作。SearchCaseLibraryUseCase 提供案例庫的向量搜尋能力（供 L1 使用）；IngestManualUseCase 處理 PDF 手冊的上傳、解析（PyMuPDF）、切片、向量化（text-embedding-004）及入庫流程（供 L2 RAG 使用）。

---

### 規格 4-1: `search_case_library`

**描述 (Description)**: 將查詢文字向量化後，對 `case_entries` 表執行 pgvector cosine similarity 搜尋，回傳匹配的案例清單。

**函式簽名**:
```python
async def search_case_library(
    self,
    query: KBSearchQueryDTO,
) -> KBSearchResultDTO:
```

其中 `KBSearchQueryDTO` 包含:
```python
class KBSearchQueryDTO:
    query_text: str          # 搜尋文字
    brand: str | None        # 品牌過濾 (optional)
    lock_type: str | None    # 鎖型過濾 (optional)
    top_k: int = 3           # 回傳筆數上限
    threshold: float = 0.85  # 相似度閾值
```

**契約式設計 (Design by Contract, DbC)**:

*   **前置條件 (Preconditions)**:
    1. `query.query_text` 不可為空字串，長度不超過 2000 字元。
    2. `query.top_k` 範圍為 `1 ~ 10`。
    3. `query.threshold` 範圍為 `0.0 ~ 1.0`。
    4. Embedding Service 可用。
    5. PostgreSQL + pgvector 連線可用。

*   **後置條件 (Postconditions)**:
    1. 回傳的 `KBSearchResultDTO` 包含 `results`（案例清單）與 `total_found`（符合閾值的總數）。
    2. `results` 中每筆的 `similarity_score >= threshold`，按 score 降序排列。
    3. `results` 最多 `top_k` 筆。
    4. 每筆結果包含 `case_entry_id`, `title`, `problem_description`, `solution`, `similarity_score`, `brand`, `lock_type`, `difficulty`。
    5. 搜尋耗時（含 embedding 生成 + pgvector 查詢）記錄於回傳 DTO 的 `search_duration_ms`。

*   **不變性 (Invariants)**:
    1. 只搜尋 `is_active = true` 的案例。
    2. Embedding 維度為 768。
    3. 搜尋操作為唯讀，不修改任何資料（`hit_count` 更新由 ThreeLayerResolver 負責）。

---

### 規格 4-2: `ingest_manual`

**描述 (Description)**: 接收管理員上傳的 PDF 手冊檔案，執行非同步處理流程：PDF 解析 -> 文本切片 -> Embedding 向量化 -> 入庫。

**函式簽名**:
```python
async def ingest_manual(
    self,
    file: UploadFile,
    brand: str,
    model: str | None = None,
    uploaded_by: uuid.UUID | None = None,
) -> ManualIngestResponseDTO:
```

**契約式設計 (Design by Contract, DbC)**:

*   **前置條件 (Preconditions)**:
    1. `file` 必須為有效的 PDF 檔案（MIME type 為 `application/pdf`）。
    2. `file` 大小不超過 50MB。
    3. `brand` 不可為空字串。
    4. `uploaded_by`（若提供）必須對應一個存在且 `role` 為 `"admin"` 或 `"reviewer"` 的使用者。

*   **後置條件 (Postconditions)**:
    1. `manuals` 表新增一筆記錄，`status = "processing"`。
    2. 非同步背景任務已啟動，執行以下 Pipeline：
        a. PDF 解析（PyMuPDF）：提取文本與頁碼。
        b. 文本切片：按章節 + 固定 Token 數（約 512 tokens/chunk，重疊 50 tokens）切割。
        c. 向量化：對每個 chunk 呼叫 Embedding Service 生成 768 維向量。
        d. 入庫：所有 chunks 批次寫入 `manual_chunks` 表。
    3. Pipeline 完成後：`manuals.status` 更新為 `"completed"`，`total_chunks` 更新為實際切片數。
    4. Pipeline 失敗時：`manuals.status` 更新為 `"failed"`，`error_message` 記錄失敗原因。
    5. 回傳的 `ManualIngestResponseDTO` 包含 `manual_id` 與 `status = "processing"`（非同步處理中）。

*   **不變性 (Invariants)**:
    1. 每個 `manual_chunks` 的 `embedding` 維度始終為 768。
    2. `manual_chunks.chunk_index` 在同一 `manual_id` 下連續且唯一（從 0 開始）。
    3. `manual_chunks.token_count` 不超過切片上限（預設 512 + 50 重疊 = 562）。
    4. PDF 處理流程不阻塞 API 回應（全程非同步）。

---

### 測試情境與案例 (KnowledgeBaseManager)

#### 情境 1: 正常路徑 — 向量搜尋命中高相似度案例

*   **測試案例 ID**: `TC-KBM-001`
*   **描述**: 搜尋 "Yale YDM-7116 密碼鍵盤無回應"，案例庫中有完全匹配的案例。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - 在 `case_entries` 表中預置一筆案例：`title = "Yale YDM-7116 密碼鍵盤無回應"`，`embedding` 已計算。
        - Mock Embedding Service 為搜尋文字生成對應的 768 維向量。
    2.  **Act**: 呼叫 `search_case_library(KBSearchQueryDTO(query_text="Yale YDM-7116 密碼鍵盤沒反應", brand="Yale", top_k=3, threshold=0.85))`。
    3.  **Assert**:
        - 驗證 `results` 至少包含 1 筆記錄。
        - 驗證第一筆結果的 `similarity_score >= 0.85`。
        - 驗證 `solution` 欄位非空。
        - 驗證 `search_duration_ms` 為正整數。

#### 情境 2: 正常路徑 — 搜尋無命中（所有結果低於閾值）

*   **測試案例 ID**: `TC-KBM-002`
*   **描述**: 搜尋一個案例庫中完全沒有相關資料的問題，回傳空結果。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - `case_entries` 表中只有與 Yale 相關的案例。
        - 搜尋文字為 `"未知品牌 XYZ-999 型號的全新問題"`。
    2.  **Act**: 呼叫 `search_case_library(KBSearchQueryDTO(query_text="未知品牌 XYZ-999 的問題", threshold=0.85))`。
    3.  **Assert**:
        - 驗證 `results` 為空列表。
        - 驗證 `total_found` 為 0。

#### 情境 3: 正常路徑 — PDF 手冊上傳與切片處理

*   **測試案例 ID**: `TC-KBM-003`
*   **描述**: 管理員上傳一份 Samsung SHP-DP609 的操作手冊 PDF，系統應完成解析、切片與向量化。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - 準備一份測試用 PDF 檔案（10 頁，約 5000 字）。
        - Mock Embedding Service 的 batch embedding API。
    2.  **Act**: 呼叫 `ingest_manual(file=test_pdf, brand="Samsung", model="SHP-DP609", uploaded_by=admin_user_id)`。
    3.  **Assert**:
        - 驗證 `manuals` 表新增一筆記錄，`brand = "Samsung"`, `model = "SHP-DP609"`。
        - 驗證回傳的 `status` 為 `"processing"`。
        - 等待非同步任務完成後：
            - 驗證 `manuals.status` 為 `"completed"`。
            - 驗證 `manual_chunks` 表中新增了多筆記錄（每筆 `token_count <= 562`）。
            - 驗證每筆 chunk 的 `embedding` 維度為 768。
            - 驗證 `chunk_index` 從 0 開始連續遞增。

#### 情境 4: 邊界情況 — 品牌過濾縮小搜尋範圍

*   **測試案例 ID**: `TC-KBM-004`
*   **描述**: 當指定 `brand` 過濾時，搜尋結果應優先展示該品牌的案例。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - `case_entries` 表中有兩筆相似案例：一筆 `brand = "Yale"`，一筆 `brand = "Samsung"`，問題描述相近。
    2.  **Act**: 呼叫 `search_case_library(KBSearchQueryDTO(query_text="密碼鍵盤無回應", brand="Yale"))`。
    3.  **Assert**:
        - 驗證結果中 Yale 品牌的案例排在 Samsung 之前（假設 similarity 相近時品牌匹配有加分）。

#### 情境 5: 無效輸入 — 上傳非 PDF 檔案

*   **測試案例 ID**: `TC-KBM-005`
*   **描述**: 管理員嘗試上傳一份 `.docx` 檔案，系統應拒絕。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**: 準備一份 `.docx` 檔案。
    2.  **Act**: 呼叫 `ingest_manual(file=docx_file, brand="Yale")`。
    3.  **Assert**:
        - 預期系統拋出 `ValidationError`，訊息包含 `"PDF"` 或 `"file format"`。
        - 驗證 `manuals` 表未新增任何記錄。

#### 情境 6: 無效輸入 — 超過大小限制的 PDF

*   **測試案例 ID**: `TC-KBM-006`
*   **描述**: 管理員上傳超過 50MB 的 PDF 檔案，系統應拒絕。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**: Mock 一份 55MB 的 PDF UploadFile。
    2.  **Act**: 呼叫 `ingest_manual(file=large_pdf, brand="Yale")`。
    3.  **Assert**:
        - 預期系統拋出 `ValidationError`，訊息包含 `"file size"` 或 `"50MB"`。

#### 情境 7: 業務規則 — 已停用的案例不出現在搜尋結果

*   **測試案例 ID**: `TC-KBM-007`
*   **描述**: 管理員將某案例的 `is_active` 設為 `false` 後，該案例不應出現在向量搜尋結果中。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - `case_entries` 表中有一筆高相似度案例，但 `is_active = false`。
    2.  **Act**: 呼叫 `search_case_library` 搜尋與該案例完全匹配的文字。
    3.  **Assert**:
        - 驗證搜尋結果中不包含該停用案例。

#### 情境 8: 業務規則 — PDF 處理失敗的錯誤記錄

*   **測試案例 ID**: `TC-KBM-008`
*   **描述**: PDF 內容損壞導致解析失敗，系統應記錄錯誤但不影響其他操作。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**: Mock PyMuPDF 解析時拋出例外。
    2.  **Act**: 呼叫 `ingest_manual(file=corrupted_pdf, brand="Yale")`。
    3.  **Assert**:
        - 驗證 `manuals.status` 最終為 `"failed"`。
        - 驗證 `manuals.error_message` 非空，記錄了失敗原因。
        - 驗證 `manual_chunks` 表中無對應的切片記錄。
        - 驗證系統未拋出未捕獲的例外。

---

## 模組 5: SOPGenerator (DraftSOPUseCase)

**所在路徑**: `backend/src/smart_lock/application/knowledge_base/use_cases.py`
**對應領域層**: `backend/src/smart_lock/domains/knowledge_base/entities.py` (SOPDraft)
**對應 BDD Feature**: `docs/03_behavior_driven_development.md#feature-自進化知識庫`
**對應資料庫表**: `sop_drafts`, `case_entries`

**模組描述**: SOPGenerator 是自演化知識庫的核心。當案件成功解決且使用者回饋為正面時，系統自動從對話記錄與 ProblemCard 中萃取解決模式，利用 LLM 生成結構化 SOP 草稿。草稿經管理員審核後，可一鍵發布為正式案例條目，使知識庫持續成長。

---

### 規格 5-1: `draft_sop`

**描述 (Description)**: 從已解決的案件中自動生成 SOP 草稿，包含標題、適用條件、步驟與注意事項。

**函式簽名**:
```python
async def draft_sop(
    self,
    conversation_id: uuid.UUID,
    problem_card_id: uuid.UUID,
) -> SOPDraftResponseDTO:
```

**契約式設計 (Design by Contract, DbC)**:

*   **前置條件 (Preconditions)**:
    1. `conversation_id` 對應的 `conversations` 記錄存在，且 `status` 為 `"resolved"`。
    2. `problem_card_id` 對應的 `problem_cards` 記錄存在，且 `resolution_layer` 不為 null。
    3. 對話中存在至少一則 `role = "assistant"` 的回覆，包含解決方案內容。
    4. 使用者回饋 (`conversations.user_feedback`) 為 `"helpful"`（僅對正面回饋的案件生成 SOP）。
    5. LLMGateway 服務可用。

*   **後置條件 (Postconditions)**:
    1. `sop_drafts` 表新增一筆記錄，`status = "pending_review"`。
    2. `title` 以 `"{brand} {model} {symptom_summary}"` 格式自動生成。
    3. `steps` JSONB 為有序陣列，每個元素包含 `step_number`, `description`, `notes`。
    4. `source_conversation_id` 與 `source_problem_card_id` 正確關聯。
    5. 若為 L3 人工解決的案件，SOP 草稿應區分 `temporary_fix` 與 `permanent_fix` 區段。
    6. 管理員通知已發送（Dashboard 通知或其他機制）。
    7. 回傳的 `SOPDraftResponseDTO` 包含 `sop_draft_id` 與完整草稿內容。

*   **不變性 (Invariants)**:
    1. SOP 草稿不可自動發布，必須經過管理員審核。
    2. `steps` 陣列至少包含 1 個步驟。
    3. 同一 `conversation_id` 不應重複生成 SOP 草稿。

---

### 規格 5-2: `check_duplicate`

**描述 (Description)**: 在提交 SOP 草稿供審核前，檢查知識庫中是否已存在高度相似的案例或 SOP，避免重複。

**函式簽名**:
```python
async def check_duplicate(
    self,
    sop_title: str,
    sop_steps_text: str,
    similarity_threshold: float = 0.90,
) -> DuplicateCheckResultDTO:
```

**契約式設計 (Design by Contract, DbC)**:

*   **前置條件 (Preconditions)**:
    1. `sop_title` 不可為空字串。
    2. `sop_steps_text` 不可為空字串（將 steps JSONB 序列化為純文字）。
    3. `similarity_threshold` 範圍為 `0.0 ~ 1.0`，預設 0.90。
    4. Embedding Service 可用。

*   **後置條件 (Postconditions)**:
    1. 回傳的 `DuplicateCheckResultDTO` 包含 `is_duplicate`（布林值）與 `similar_entries`（相似案例列表）。
    2. 若 `is_duplicate = True`，`similar_entries` 中至少有一筆 `similarity_score >= similarity_threshold` 的案例。
    3. `similar_entries` 包含 `case_entry_id`, `title`, `similarity_score`，按 score 降序排列。
    4. 同時搜尋 `case_entries` 與 `sop_drafts`（status 為 `"pending_review"` 或 `"approved"`）中的已有內容。

*   **不變性 (Invariants)**:
    1. 此方法為查詢操作，不修改任何資料。
    2. 重複檢查基於語義相似度（向量比對），而非精確文字比對。

---

### 測試情境與案例 (SOPGenerator)

#### 情境 1: 正常路徑 — 從 L2 解決的案件生成 SOP 草稿

*   **測試案例 ID**: `TC-SOP-001`
*   **描述**: 一個透過 L2 RAG 成功解決的案件，使用者回饋為正面，系統應自動生成 SOP 草稿。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - 已存在 `conversations` 記錄：`status = "resolved"`, `resolution_layer = "L2"`, `user_feedback = "helpful"`。
        - 已存在 `problem_cards` 記錄：`brand = "Samsung"`, `model = "SHP-DP609"`, `symptoms = ["wifi_connection_fail"]`, `resolution_layer = "L2"`。
        - 對話記錄包含 AI 生成的解決方案步驟。
        - Mock `LLMGateway` 從對話記錄中生成結構化 SOP。
    2.  **Act**: 呼叫 `draft_sop(conversation_id, problem_card_id)`。
    3.  **Assert**:
        - 驗證 `sop_drafts` 表新增一筆記錄。
        - 驗證 `title` 包含 `"Samsung"`, `"SHP-DP609"`, `"WiFi"` 相關語意。
        - 驗證 `steps` JSONB 為非空有序陣列。
        - 驗證 `status` 為 `"pending_review"`。
        - 驗證 `source_conversation_id` 與 `source_problem_card_id` 正確設定。

#### 情境 2: 正常路徑 — 從 L3 人工解決的案件生成包含臨時/永久修復的 SOP

*   **測試案例 ID**: `TC-SOP-002`
*   **描述**: L3 人工客服解決的案件中，客服紀錄同時包含臨時修復與根本修復方案，SOP 應區分兩個區段。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - `conversations.resolution_layer = "L3"`, `user_feedback = "helpful"`。
        - 對話記錄中人工客服的解決方案包含 `"暫時解決"` 與 `"根本解決"` 兩部分。
    2.  **Act**: 呼叫 `draft_sop(conversation_id, problem_card_id)`。
    3.  **Assert**:
        - 驗證 `steps` JSONB 中包含 `"temporary_fix"` 和 `"permanent_fix"` 兩個區段。
        - 驗證 `notes` 中包含 `"requires_technician: true"` 標記（需派技師到場）。

#### 情境 3: 邊界情況 — 重複檢測發現高相似度既有案例

*   **測試案例 ID**: `TC-SOP-003`
*   **描述**: 即將生成的 SOP 與已有案例的相似度 >= 0.90，系統應標記為重複並建議合併。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - `case_entries` 表中已有 `"Yale YDM-7116 密碼鍵盤無回應"` 的案例。
        - 準備生成一份幾乎相同問題的 SOP 草稿。
        - Mock Embedding Service 計算兩者向量的 cosine similarity 為 0.92。
    2.  **Act**: 呼叫 `check_duplicate(sop_title="Yale YDM-7116 按鍵沒反應", sop_steps_text="...")`。
    3.  **Assert**:
        - 驗證 `is_duplicate = True`。
        - 驗證 `similar_entries` 至少包含 1 筆，`similarity_score >= 0.90`。
        - 驗證相似案例的 `case_entry_id` 與 `title` 正確回傳。

#### 情境 4: 邊界情況 — 同一對話不可重複生成 SOP

*   **測試案例 ID**: `TC-SOP-004`
*   **描述**: 同一 `conversation_id` 已生成過 SOP 草稿，再次呼叫應被拒絕。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - `sop_drafts` 表中已有一筆 `source_conversation_id` 匹配的記錄。
    2.  **Act**: 呼叫 `draft_sop(conversation_id, problem_card_id)`。
    3.  **Assert**:
        - 預期系統拋出 `ValidationError` 或回傳已存在的 SOP draft（而非建立新的）。
        - 驗證 `sop_drafts` 表中該 conversation 的記錄數仍為 1。

#### 情境 5: 無效輸入 — 案件未解決即嘗試生成 SOP

*   **測試案例 ID**: `TC-SOP-005`
*   **描述**: 對話 `status` 不是 `"resolved"` 時嘗試生成 SOP，系統應拒絕。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - `conversations.status = "collecting"`（尚在收集資訊階段）。
    2.  **Act**: 呼叫 `draft_sop(conversation_id, problem_card_id)`。
    3.  **Assert**:
        - 預期系統拋出 `ValidationError`，訊息包含 `"conversation must be resolved"`。
        - 驗證 `sop_drafts` 表未新增記錄。

#### 情境 6: 無效輸入 — 使用者回饋為負面時不生成 SOP

*   **測試案例 ID**: `TC-SOP-006`
*   **描述**: 使用者回饋 `user_feedback = "not_helpful"`，系統不應為負面回饋的案件生成 SOP。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - `conversations.status = "resolved"`, `user_feedback = "not_helpful"`。
    2.  **Act**: 呼叫 `draft_sop(conversation_id, problem_card_id)`。
    3.  **Assert**:
        - 預期系統拋出 `ValidationError`，訊息包含 `"positive feedback required"` 或類似語意。
        - 驗證 `sop_drafts` 表未新增記錄。

#### 情境 7: 業務規則 — SOP 發布後自動轉為案例條目

*   **測試案例 ID**: `TC-SOP-007`
*   **描述**: 管理員審核通過並發布 SOP 後，系統應自動將其向量化並加入 `case_entries` 表。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - 已存在 `sop_drafts` 記錄，`status = "approved"`。
        - Mock Embedding Service 為 SOP 內容生成 768 維向量。
    2.  **Act**: 呼叫 `adopt_sop_as_case(sop_draft_id)` （AdoptSOPAsCaseUseCase）。
    3.  **Assert**:
        - 驗證 `case_entries` 表新增一筆記錄。
        - 驗證新案例的 `source = "sop_approved"`。
        - 驗證新案例的 `embedding` 維度為 768。
        - 驗證新案例的 `is_active = true`。
        - 驗證 `sop_drafts.status` 更新為 `"published"`。
        - 驗證 `sop_drafts.published_as_case_entry_id` 指向新建的案例條目。
        - 驗證新案例在後續的 L1 向量搜尋中可被命中。

#### 情境 8: 業務規則 — 管理員退回 SOP 時記錄回饋

*   **測試案例 ID**: `TC-SOP-008`
*   **描述**: 管理員審核退回 SOP 草稿並附上修訂意見，系統應記錄回饋並嘗試重新生成。
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - 已存在 `sop_drafts` 記錄，`status = "pending_review"`。
    2.  **Act**: 呼叫 `review_sop_draft(sop_draft_id, decision="reject", comment="步驟缺少安全提醒，需補充斷電注意事項")`。
    3.  **Assert**:
        - 驗證 `sop_drafts.status` 更新為 `"rejected"`。
        - 驗證 `sop_drafts.review_comment` 包含管理員的回饋。
        - 驗證 `sop_drafts.reviewed_by` 記錄審核者 ID。
        - 驗證 `sop_drafts.reviewed_at` 記錄審核時間。

---

## 附錄 A: 測試案例 ID 索引

| 測試案例 ID | 模組 | 情境分類 | 簡述 |
|:---|:---|:---|:---|
| TC-CM-001 | ConversationManager | Happy Path | 新使用者首次發送問題訊息 |
| TC-CM-002 | ConversationManager | Happy Path | 多輪對話逐步收集 ProblemCard 資訊 |
| TC-CM-003 | ConversationManager | Happy Path | 資訊收集完成觸發三層解決引擎 |
| TC-CM-004 | ConversationManager | Edge Case | 對話超時後恢復 |
| TC-CM-005 | ConversationManager | Invalid Input | 使用者發送不相關訊息 |
| TC-CM-006 | ConversationManager | Invalid Input | LINE User ID 格式不合法 |
| TC-CM-007 | ConversationManager | Business Rule | LINE Webhook 非同步處理保證 1 秒回應 |
| TC-CM-008 | ConversationManager | Business Rule | 同一使用者並行對話限制 |
| TC-PCE-001 | ProblemCardEngine | Happy Path | 所有欄位齊全時生成完整 ProblemCard |
| TC-PCE-002 | ProblemCardEngine | Happy Path | 僅有品牌與症狀的最低限度 ProblemCard |
| TC-PCE-003 | ProblemCardEngine | Edge Case | 停產型號處理 |
| TC-PCE-004 | ProblemCardEngine | Edge Case | 重複生成 ProblemCard 冪等性 |
| TC-PCE-005 | ProblemCardEngine | Invalid Input | 空的對話訊息列表 |
| TC-PCE-006 | ProblemCardEngine | Business Rule | 優先度自動分類 |
| TC-TLR-001 | ThreeLayerResolver | Happy Path | L1 高信心命中直接解決 |
| TC-TLR-002 | ThreeLayerResolver | Happy Path | L1 未命中，L2 RAG 成功解決 |
| TC-TLR-003 | ThreeLayerResolver | Happy Path | L1 和 L2 均失敗，升級至 L3 |
| TC-TLR-004 | ThreeLayerResolver | Edge Case | L1 多個接近閾值的模糊匹配 |
| TC-TLR-005 | ThreeLayerResolver | Edge Case | L1 閾值邊界值行為 |
| TC-TLR-006 | ThreeLayerResolver | Invalid Input | ProblemCard 未達最低完整度 |
| TC-TLR-007 | ThreeLayerResolver | Business Rule | L3 非營業時間升級 |
| TC-TLR-008 | ThreeLayerResolver | Business Rule | Embedding Service 不可用時降級 |
| TC-KBM-001 | KnowledgeBaseManager | Happy Path | 向量搜尋命中高相似度案例 |
| TC-KBM-002 | KnowledgeBaseManager | Happy Path | 搜尋無命中 |
| TC-KBM-003 | KnowledgeBaseManager | Happy Path | PDF 手冊上傳與切片處理 |
| TC-KBM-004 | KnowledgeBaseManager | Edge Case | 品牌過濾縮小搜尋範圍 |
| TC-KBM-005 | KnowledgeBaseManager | Invalid Input | 上傳非 PDF 檔案 |
| TC-KBM-006 | KnowledgeBaseManager | Invalid Input | 超過大小限制的 PDF |
| TC-KBM-007 | KnowledgeBaseManager | Business Rule | 已停用案例不出現在搜尋結果 |
| TC-KBM-008 | KnowledgeBaseManager | Business Rule | PDF 處理失敗的錯誤記錄 |
| TC-SOP-001 | SOPGenerator | Happy Path | 從 L2 解決案件生成 SOP 草稿 |
| TC-SOP-002 | SOPGenerator | Happy Path | 從 L3 案件生成包含臨時/永久修復的 SOP |
| TC-SOP-003 | SOPGenerator | Edge Case | 重複檢測發現高相似度既有案例 |
| TC-SOP-004 | SOPGenerator | Edge Case | 同一對話不可重複生成 SOP |
| TC-SOP-005 | SOPGenerator | Invalid Input | 案件未解決即嘗試生成 SOP |
| TC-SOP-006 | SOPGenerator | Invalid Input | 使用者回饋為負面時不生成 SOP |
| TC-SOP-007 | SOPGenerator | Business Rule | SOP 發布後自動轉為案例條目 |
| TC-SOP-008 | SOPGenerator | Business Rule | 管理員退回 SOP 時記錄回饋 |

---

## 附錄 B: 測試覆蓋度對照表

| 模組 | Happy Path | Edge Case | Invalid Input | Business Rule | 合計 |
|:---|:---:|:---:|:---:|:---:|:---:|
| ConversationManager | 3 | 1 | 2 | 2 | 8 |
| ProblemCardEngine | 2 | 2 | 1 | 1 | 6 |
| ThreeLayerResolver | 3 | 2 | 1 | 2 | 8 |
| KnowledgeBaseManager | 3 | 1 | 2 | 2 | 8 |
| SOPGenerator | 2 | 2 | 2 | 2 | 8 |
| **合計** | **13** | **8** | **8** | **9** | **38** |

---

## 附錄 C: LLM Prompting Guide

在 TDD 開發流程中，可使用以下 Prompt 範本請 LLM 生成初始的失敗測試：

```
「請根據以下的測試案例規格，為我生成一個會失敗的 TDD 單元測試（pytest + pytest-asyncio）。

目標框架：FastAPI + SQLAlchemy 2.0 async + pgvector
目標函式：[函式名稱]
測試案例 ID：[TC-XXX-NNN]

規格如下：
[貼上對應的測試案例文本，包含 Arrange-Act-Assert]

請使用以下 Mock 工具：unittest.mock.AsyncMock
Repository 介面使用 Protocol（非 ABC）。
確保測試為 async def，使用 @pytest.mark.asyncio 裝飾器。」
```

---

**文件結尾**

*本文件為 V1.0 核心模組的模組規格與測試案例定義。V2.0 派工與帳務模組（DispatchEngine, PricingEngine, AccountingModule）的規格將在 V2.0 設計階段補充。*
