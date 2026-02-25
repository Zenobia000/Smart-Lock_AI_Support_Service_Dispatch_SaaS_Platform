-- ============================================================================
-- Smart Lock AI Support & Service Dispatch SaaS Platform
-- PostgreSQL Schema Definition
-- ============================================================================
--
-- 版本：v1.1
-- 更新日期：2026-02-25
-- 參考文件：
--   - docs/02_project_brief_and_prd.md          (PRD & User Stories)
--   - docs/05_architecture_and_design_document.md (§5.1 數據模型, §5.4 向量索引策略)
--   - docs/06_api_design_specification.md        (API Schema 定義)
--   - docs/08_project_structure_guide.md         (DDD 領域劃分)
--
-- 核心表格群組：
--   [1] users              — 使用者管理 (含 LINE Profile 儲存邏輯)
--   [2] conversations      — 對話 (Chats) Session 管理
--       messages           — 對話訊息記錄
--   [3] problem_cards      — 結構化問題診斷卡
--   [4] manuals            — 產品手冊管理
--       manual_chunks      — 手冊切片 (RAG 語義搜尋用)
--   [5] case_entries       — 案例庫 (三層引擎 L1 向量搜尋)
--   [6] sop_drafts         — SOP 草稿 (自進化知識庫)
--   [V2.0] technicians, work_orders, price_rules, invoices,
--          reconciliations, settlements
--
-- 向量維度：768 (Google text-embedding-004)
-- 向量索引：HNSW (m=16, ef_construction=64, cosine similarity)
-- ============================================================================


-- ============================================================================
-- 系統準備與擴展套件
-- ============================================================================

-- 啟用 UUID 生成函數
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 啟用 pgvector 擴展套件 (用於 AI 向量相似度搜尋，依據 ADR-002)
CREATE EXTENSION IF NOT EXISTS vector;


-- ============================================================================
-- 自動更新 updated_at 的共用 Trigger Function
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- [1] 使用者管理 (User Management)
-- ============================================================================
--
-- ┌─────────────────────────────────────────────────────────────────────────┐
-- │ User Profile 儲存邏輯 (LINE ID, Display Name)                          │
-- ├─────────────────────────────────────────────────────────────────────────┤
-- │                                                                         │
-- │ ■ 首次互動 (Follow Event / 第一則訊息)：                                │
-- │   1. LINE Webhook 送來 source.userId (格式: U + 32 位 hex)              │
-- │   2. 呼叫 LINE Get Profile API 取得完整 Profile：                       │
-- │      - displayName  → users.display_name                                │
-- │      - pictureUrl   → users.picture_url                                 │
-- │      - statusMessage→ users.status_message                              │
-- │   3. INSERT INTO users，role = 'line_user'                              │
-- │                                                                         │
-- │ ■ 後續互動：                                                            │
-- │   1. 以 line_user_id 查詢 users 表 (WHERE line_user_id = ?)            │
-- │   2. 若 profile_updated_at 距今 > 24 小時，重新呼叫 Get Profile API     │
-- │      同步 display_name, picture_url, status_message                     │
-- │      (LINE 使用者可隨時更改顯示名稱與大頭貼)                            │
-- │   3. 更新 last_active_at 為當前時間                                     │
-- │                                                                         │
-- │ ■ L3 轉人工 / 派工時：                                                  │
-- │   AI 對話流程中向消費者收集 phone, email, address 等進階資訊            │
-- │   UPDATE users SET phone = ?, email = ?, address = ?                    │
-- │                                                                         │
-- │ ■ 管理員 / 技師帳號：                                                   │
-- │   透過 Admin Panel 建立，line_user_id 可為 NULL                         │
-- │   role 設定為 'admin' / 'reviewer' / 'technician'                       │
-- │                                                                         │
-- │ ■ line_user_id 特性：                                                   │
-- │   - 由 LINE Platform 產生，永久不變                                     │
-- │   - 格式固定為 U + 32 位十六進位字元 (共 33 字元)                       │
-- │   - 同一使用者在不同 LINE Official Account 下有不同 ID                  │
-- │   - 這是辨識消費者身分的唯一依據                                        │
-- └─────────────────────────────────────────────────────────────────────────┘

CREATE TABLE users (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- LINE Profile 欄位
    line_user_id        VARCHAR(255) UNIQUE,            -- LINE Platform User ID (U + 32 hex chars)
    display_name        VARCHAR(255),                   -- LINE 顯示名稱 (可被使用者隨時更改)
    picture_url         VARCHAR(512),                   -- LINE 大頭貼 URL
    status_message      VARCHAR(500),                   -- LINE 狀態訊息

    -- 進階聯絡資訊 (L3 轉人工或派工時收集)
    phone               VARCHAR(50),
    email               VARCHAR(255),
    address             TEXT,                           -- V2.0 派工用地址

    -- 系統欄位
    role                VARCHAR(50) NOT NULL DEFAULT 'line_user',
                        -- 'line_user'   : LINE 一般消費者
                        -- 'admin'       : 總部管理員
                        -- 'reviewer'    : SOP 審核員
                        -- 'technician'  : 維修技師 (V2.0)
    is_active           BOOLEAN DEFAULT TRUE,           -- 帳號啟用狀態
    last_active_at      TIMESTAMP WITH TIME ZONE,       -- 最後互動時間 (每次對話時更新)
    profile_updated_at  TIMESTAMP WITH TIME ZONE,       -- LINE Profile 最後同步時間

    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE  users IS '使用者主表：統一管理 LINE 消費者、管理員、審核員、技師四種角色';
COMMENT ON COLUMN users.line_user_id IS 'LINE Platform 唯一使用者 ID (U + 32 hex)，消費者的唯一識別依據';
COMMENT ON COLUMN users.display_name IS 'LINE 顯示名稱，使用者可隨時變更，系統定期同步更新';
COMMENT ON COLUMN users.picture_url IS 'LINE 大頭貼圖片 URL，由 Get Profile API 取得';
COMMENT ON COLUMN users.profile_updated_at IS '最後一次從 LINE Get Profile API 同步 profile 資料的時間';

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- [2] 對話管理 (Conversations / Chats)
-- ============================================================================
--
-- 設計要點：
--   - 一次 Chat Session 對應一筆 Conversation 記錄
--   - 每個 Conversation 包含多個 Messages (1:N)
--   - 每個 Conversation 對應至多一張 ProblemCard (1:1)
--   - session_id 同時作為 Redis Session Cache 的 key
--   - 對話超時策略：30 分鐘無互動 → status 轉為 'expired'
-- ============================================================================

CREATE TABLE conversations (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id          VARCHAR(255) UNIQUE NOT NULL,   -- 對應 Redis session key

    status              VARCHAR(50) NOT NULL DEFAULT 'active',
                        -- 'active'     : 對話進行中
                        -- 'collecting' : 正在收集 ProblemCard 資訊
                        -- 'resolving'  : 三層解決引擎處理中
                        -- 'resolved'   : 已解決 (自助)
                        -- 'escalated'  : 已轉人工 / 已建立派工
                        -- 'expired'    : 對話超時 (30 分鐘無互動)
    channel             VARCHAR(50) DEFAULT 'line',     -- 來源管道: 'line', 'web', 'api'
    context             JSONB,                          -- 多輪對話上下文暫存
                                                        -- {intent, collected_fields, missing_fields,
                                                        --  conversation_summary, turn_count, ...}
    resolution_layer    VARCHAR(10),                    -- 最終解決層級: 'L1', 'L2', 'L3'
    user_feedback       VARCHAR(20),                    -- 消費者回饋: 'helpful', 'not_helpful'
    message_count       INTEGER DEFAULT 0,

    started_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at         TIMESTAMP WITH TIME ZONE,
    expired_at          TIMESTAMP WITH TIME ZONE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE  conversations IS '對話 Session 主表 (Chats)：追蹤消費者與 AI 客服的完整對話生命週期';
COMMENT ON COLUMN conversations.session_id IS '對話 session 唯一識別碼，同步作為 Redis Session Cache 的 key';
COMMENT ON COLUMN conversations.context IS '多輪對話上下文 JSON，含已識別意圖、已收集欄位、缺失欄位等';
COMMENT ON COLUMN conversations.user_feedback IS '消費者對 AI 解決方案的回饋 (US-011)';

CREATE TRIGGER trg_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


CREATE TABLE messages (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id     UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    role                VARCHAR(50) NOT NULL,
                        -- 'user'       : 消費者訊息
                        -- 'assistant'  : AI 客服回覆
                        -- 'system'     : 系統訊息 (狀態變更、轉接通知等)
    content_type        VARCHAR(50) DEFAULT 'text',
                        -- 'text'       : 純文字
                        -- 'image'      : 圖片 (搭配 Vision AI 分析)
                        -- 'location'   : 位置資訊
                        -- 'flex'       : LINE Flex Message
    content             TEXT NOT NULL,                   -- 訊息內容 (文字 / JSON / URL)
    metadata            JSONB,                          -- 擴展資訊：
                                                        -- {token_usage, latency_ms, image_url,
                                                        --  vision_analysis, line_message_id, ...}

    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE  messages IS '對話訊息表：記錄每輪對話的完整內容、角色與元資訊';
COMMENT ON COLUMN messages.metadata IS '擴展元資訊 JSON：token 用量、回應延遲、圖片 URL、Vision 分析結果等';


-- ============================================================================
-- [3] 結構化問題診斷卡 (ProblemCard)
-- ============================================================================
--
-- 設計要點：
--   - 每個 Conversation 產生至多一張 ProblemCard (1:1，UNIQUE FK)
--   - AI 從多輪對話中漸進式擷取欄位 (brand, model, symptoms 等)
--   - completeness_score 反映關鍵欄位的填充率 (0.0 ~ 1.0)
--   - 當 ProblemCard 資訊充足 → 觸發三層解決引擎
--   - 生成後以 LINE Flex Message 展示給消費者確認 (US-006)
--
-- ProblemCard 必填欄位 (completeness 計算依據)：
--   brand + symptoms (至少這兩個欄位) → 可觸發解決引擎
--   model, location, door_status, network_status → 補充資訊，提升匹配精度
-- ============================================================================

CREATE TABLE problem_cards (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id     UUID UNIQUE REFERENCES conversations(id) ON DELETE CASCADE,

    -- 電子鎖資訊 (AI 從對話中擷取)
    brand               VARCHAR(100),                   -- 品牌: Yale, Samsung, Gateman, Philips...
    model               VARCHAR(100),                   -- 型號: YDM-4109, SHP-DP609...
    category            VARCHAR(100),                   -- 問題類別: 電池, WiFi, 密碼, 安裝, 故障, 其他
    location            VARCHAR(255),                   -- 地址或區域

    -- 狀態描述
    door_status         VARCHAR(50),
                        -- 'locked_out'           : 被鎖在外面
                        -- 'partially_functional' : 部分功能異常
                        -- 'normal'               : 門鎖正常 (諮詢類)
                        -- 'unknown'              : 未確認
    network_status      VARCHAR(50),
                        -- 'online'  : 連網正常
                        -- 'offline' : 離線
                        -- 'unknown' : 未確認
    symptoms            JSONB,                          -- 症狀 JSON 陣列
                                                        -- ["no_response", "beeping", "battery_low"]
    urgency             VARCHAR(50) DEFAULT 'normal',
                        -- 'low'     : 一般諮詢
                        -- 'normal'  : 標準報修
                        -- 'high'    : 緊急 (被鎖在外)
                        -- 'urgent'  : 非常緊急 (安全問題)
    media_urls          JSONB,                          -- 消費者上傳的圖片/影片 URL 陣列
    intent              VARCHAR(50),
                        -- 'inquiry'   : 諮詢
                        -- 'repair'    : 報修
                        -- 'complaint' : 投訴
                        -- 'other'     : 其他

    -- 診斷狀態
    status              VARCHAR(50) DEFAULT 'incomplete',
                        -- 'incomplete' : 欄位收集中
                        -- 'confirmed'  : 消費者已確認 (Flex Message 確認)
                        -- 'resolved'   : 已解決
                        -- 'escalated'  : 已升級至人工/派工
    completeness_score  FLOAT DEFAULT 0.0,              -- 0.0 ~ 1.0，反映關鍵欄位填充率
    resolution_layer    VARCHAR(10),                    -- 最終解決層級: 'L1', 'L2', 'L3'
    extracted_fields    JSONB,                          -- AI 原始擷取結果 (含各欄位 confidence)

    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE  problem_cards IS '結構化問題診斷卡 (ProblemCard)：AI 從對話自動擷取，作為三層解決引擎的輸入核心';
COMMENT ON COLUMN problem_cards.completeness_score IS '欄位完整度分數 (0.0~1.0)，至少需要 brand + symptoms 才可觸發解決引擎';
COMMENT ON COLUMN problem_cards.extracted_fields IS 'AI 原始擷取結果 JSON，含各欄位的 confidence score';

CREATE TRIGGER trg_problem_cards_updated_at
    BEFORE UPDATE ON problem_cards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- [4] 產品手冊管理 (Manuals)
-- ============================================================================
--
-- 手冊處理流程 (Pipeline)：
--   1. 管理員上傳 PDF → INSERT manuals (status='processing')
--   2. 後台非同步解析 PDF (PyMuPDF) → 切片為 manual_chunks
--   3. 對每個 chunk 呼叫 Google Embedding API (text-embedding-004)
--      → 產生 768 維向量 → 存入 manual_chunks.embedding
--   4. 全部完成 → UPDATE manuals SET status='completed', total_chunks=N
--   5. 處理失敗 → UPDATE manuals SET status='failed', error_message='...'
--
-- 管理員可按品牌、型號分類管理手冊 (US-015)
-- 手冊上傳後顯示處理進度 (processing → indexing → completed)
-- ============================================================================

CREATE TABLE manuals (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename            VARCHAR(255) NOT NULL,          -- 原始檔名
    brand               VARCHAR(100) NOT NULL,          -- 適用品牌
    model               VARCHAR(100),                   -- 適用型號 (NULL = 品牌通用手冊)
    file_size_bytes     BIGINT,                         -- 檔案大小 (bytes)
    total_pages         INTEGER,                        -- PDF 總頁數
    total_chunks        INTEGER DEFAULT 0,              -- 切片總數

    status              VARCHAR(50) DEFAULT 'processing',
                        -- 'processing' : PDF 解析中
                        -- 'indexing'   : 向量化索引中
                        -- 'completed'  : 處理完成，可供 RAG 搜尋
                        -- 'failed'     : 處理失敗
    error_message       TEXT,                           -- 失敗時的錯誤訊息
    uploaded_by         UUID REFERENCES users(id) ON DELETE SET NULL,

    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE  manuals IS '產品手冊 PDF 主表：管理手冊上傳、解析與索引狀態';
COMMENT ON COLUMN manuals.status IS '處理狀態流轉：processing → indexing → completed / failed';


CREATE TABLE manual_chunks (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    manual_id           UUID NOT NULL REFERENCES manuals(id) ON DELETE CASCADE,

    chunk_index         INTEGER NOT NULL,               -- 在該手冊中的切片序號 (從 0 開始)
    source_pdf          VARCHAR(255),                   -- 來源 PDF 檔名
    page_number         INTEGER,                        -- 來源頁碼
    chapter_title       VARCHAR(255),                   -- 章節標題 (解析自 PDF 結構)
    content             TEXT NOT NULL,                   -- 切片文本內容
    token_count         INTEGER,                        -- 文本 token 數 (用於 LLM context 控制)

    embedding           VECTOR(768),                    -- text-embedding-004 向量 (768 維)

    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE  manual_chunks IS '手冊切片表：PDF 解析後的文本段落，含 768 維向量用於 RAG 語義搜尋';
COMMENT ON COLUMN manual_chunks.embedding IS 'Google text-embedding-004 產生的 768 維向量，用於 L2 RAG 語義搜尋';
COMMENT ON COLUMN manual_chunks.chunk_index IS '切片在手冊中的順序編號，用於還原原始閱讀順序';


-- ============================================================================
-- [5] 案例庫 (Case Entries) — 三層引擎 L1 向量搜尋
-- ============================================================================
--
-- 案例來源：
--   - manual_input  : 管理員手動新增
--   - sop_approved  : SOP 審核通過後自動納入 (US-014)
--   - imported      : CSV 批量匯入歷史案例 (US-015)
--
-- L1 搜尋邏輯：
--   1. ProblemCard 確認後，將問題描述向量化
--   2. 對 case_entries 執行 pgvector cosine similarity 搜尋
--   3. 相似度 >= 0.85 視為命中，取 Top-3 (US-008)
--   4. 命中時 hit_count += 1，回覆步驟化解決方案
-- ============================================================================

CREATE TABLE case_entries (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title               VARCHAR(255) NOT NULL,
    problem_description TEXT NOT NULL,
    solution            TEXT NOT NULL,
    brand               VARCHAR(100),                   -- 適用品牌
    lock_type           VARCHAR(100),                   -- 適用鎖型
    difficulty          VARCHAR(50) DEFAULT 'medium',   -- 'easy', 'medium', 'hard'

    embedding           VECTOR(768),                    -- text-embedding-004 向量 (768 維)

    source              VARCHAR(50) DEFAULT 'manual_input',
                        -- 'manual_input'  : 管理員手動新增
                        -- 'sop_approved'  : SOP 審核通過後自動納入
                        -- 'imported'      : CSV 批量匯入
    approved_by         UUID REFERENCES users(id) ON DELETE SET NULL,
    is_active           BOOLEAN DEFAULT TRUE,           -- 是否啟用 (支援下架)
    hit_count           INTEGER DEFAULT 0,              -- L1 搜尋命中次數

    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE  case_entries IS '案例庫：歷史成功案例與解決方案，支援 L1 向量語義搜尋 (閾值 >= 0.85)';
COMMENT ON COLUMN case_entries.embedding IS 'Google text-embedding-004 產生的 768 維向量，用於 L1 語義搜尋';
COMMENT ON COLUMN case_entries.hit_count IS 'L1 搜尋命中次數，用於統計案例使用頻率';

CREATE TRIGGER trg_case_entries_updated_at
    BEFORE UPDATE ON case_entries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- [6] SOP 草稿 (SOP Drafts) — 自進化知識庫
-- ============================================================================
--
-- 自進化流程 (US-012 ~ US-014)：
--   1. 案件狀態轉為「已解決」且消費者回饋「有幫助」→ 觸發 SOP 生成
--   2. LLM 從對話記錄與 ProblemCard 中提取 → 生成 SOP 草稿 (status='pending_review')
--   3. 管理員審核 → 'approved' 或 'rejected'
--   4. 一鍵發布 → 'published'，SOP 內容向量化後納入 case_entries
--   5. 相似度 >= 0.90 的問題不重複生成 SOP
-- ============================================================================

CREATE TABLE sop_drafts (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_conversation_id      UUID REFERENCES conversations(id) ON DELETE SET NULL,
    source_problem_card_id      UUID REFERENCES problem_cards(id) ON DELETE SET NULL,

    title                       VARCHAR(255) NOT NULL,
    applicable_conditions       TEXT,                   -- 適用條件描述
    steps                       JSONB NOT NULL,         -- SOP 步驟清單 (ordered JSON array)
    notes                       TEXT,                   -- 注意事項 / 警告

    status                      VARCHAR(50) DEFAULT 'pending_review',
                                -- 'pending_review' : 待審核
                                -- 'approved'       : 已核准
                                -- 'rejected'       : 已退回
                                -- 'published'      : 已發布至知識庫
    reviewed_by                 UUID REFERENCES users(id) ON DELETE SET NULL,
    review_comment              TEXT,
    published_as_case_entry_id  UUID REFERENCES case_entries(id) ON DELETE SET NULL,

    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    reviewed_at                 TIMESTAMP WITH TIME ZONE
);

COMMENT ON TABLE  sop_drafts IS 'SOP 草稿表：系統從成功案件自動生成，經管理員審核後可發布至案例庫';
COMMENT ON COLUMN sop_drafts.published_as_case_entry_id IS '發布後對應的 case_entries.id，建立 SOP 與案例庫的追溯關係';


-- ============================================================================
-- [V2.0] 技師與派工上下文 (Dispatch)
-- ============================================================================

CREATE TABLE technicians (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    name                VARCHAR(100) NOT NULL,
    phone               VARCHAR(50) NOT NULL,
    email               VARCHAR(255),
    capabilities        JSONB,                          -- 品牌與鎖型技能清單
    service_regions     JSONB,                          -- 可服務的地區清單
    availability        JSONB,                          -- 每週可用時段
    rating              FLOAT CHECK (rating >= 1.0 AND rating <= 5.0),
    completed_orders    INTEGER DEFAULT 0,
    status              VARCHAR(50) DEFAULT 'pending_approval',
                        -- 'pending_approval', 'active', 'inactive', 'suspended'
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER trg_technicians_updated_at
    BEFORE UPDATE ON technicians
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


CREATE TABLE work_orders (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    problem_card_id     UUID REFERENCES problem_cards(id) ON DELETE RESTRICT,
    technician_id       UUID REFERENCES technicians(id) ON DELETE SET NULL,
    created_by          UUID REFERENCES users(id) ON DELETE SET NULL,
    status              VARCHAR(50) DEFAULT 'created',
                        -- 'created', 'assigned', 'accepted', 'in_progress',
                        -- 'completed', 'confirmed', 'cancelled'
    priority            VARCHAR(50) DEFAULT 'normal',   -- 'low', 'normal', 'high', 'urgent'
    customer_name       VARCHAR(100),
    customer_phone      VARCHAR(50),
    customer_address    TEXT,
    scheduled_at        TIMESTAMP WITH TIME ZONE,
    accepted_at         TIMESTAMP WITH TIME ZONE,
    started_at          TIMESTAMP WITH TIME ZONE,
    completed_at        TIMESTAMP WITH TIME ZONE,
    service_report      TEXT,                           -- 技師完工回報
    photos              JSONB,                          -- 維修前後照片 URL 陣列
    estimated_price     FLOAT,
    final_price         FLOAT,
    rating              INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback            TEXT,
    confirmed_at        TIMESTAMP WITH TIME ZONE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER trg_work_orders_updated_at
    BEFORE UPDATE ON work_orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- [V2.0] 報價與帳務上下文 (Pricing & Accounting)
-- ============================================================================

CREATE TABLE price_rules (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    brand               VARCHAR(100) NOT NULL,
    lock_type           VARCHAR(100) NOT NULL,
    difficulty          VARCHAR(50) NOT NULL,           -- 'easy', 'medium', 'hard'
    base_price          FLOAT NOT NULL,
    labor_cost          FLOAT NOT NULL,
    parts_cost          FLOAT,
    modifiers           JSONB,                          -- 特殊加價規則 (夜間、偏遠等)
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER trg_price_rules_updated_at
    BEFORE UPDATE ON price_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


CREATE TABLE invoices (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    work_order_id       UUID UNIQUE REFERENCES work_orders(id) ON DELETE RESTRICT,
    invoice_number      VARCHAR(100) UNIQUE NOT NULL,
    amount              FLOAT NOT NULL,
    tax                 FLOAT NOT NULL DEFAULT 0,
    total               FLOAT NOT NULL,
    status              VARCHAR(50) DEFAULT 'draft',    -- 'draft', 'issued', 'paid', 'cancelled'
    line_items          JSONB NOT NULL,                 -- 報價明細清單
    issued_at           TIMESTAMP WITH TIME ZONE,
    paid_at             TIMESTAMP WITH TIME ZONE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER trg_invoices_updated_at
    BEFORE UPDATE ON invoices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


CREATE TABLE reconciliations (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    technician_id       UUID REFERENCES technicians(id) ON DELETE RESTRICT,
    period_start        TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end          TIMESTAMP WITH TIME ZONE NOT NULL,
    total_orders        INTEGER NOT NULL DEFAULT 0,
    total_revenue       FLOAT NOT NULL DEFAULT 0,
    platform_fee        FLOAT NOT NULL DEFAULT 0,
    technician_payout   FLOAT NOT NULL DEFAULT 0,
    status              VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'approved', 'disputed'
    approved_by         UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_at         TIMESTAMP WITH TIME ZONE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE settlements (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reconciliation_id   UUID REFERENCES reconciliations(id) ON DELETE RESTRICT,
    technician_id       UUID REFERENCES technicians(id) ON DELETE RESTRICT,
    amount              FLOAT NOT NULL,
    currency            VARCHAR(10) DEFAULT 'TWD',
    status              VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'paid', 'failed'
    payment_method      VARCHAR(50) DEFAULT 'bank_transfer',
    paid_at             TIMESTAMP WITH TIME ZONE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================================
-- 建立資料表索引 (參照架構文件 §5.1 表格索引策略)
-- ============================================================================

-- [users] 索引
CREATE INDEX idx_users_line_user_id ON users (line_user_id) WHERE line_user_id IS NOT NULL;
CREATE INDEX idx_users_role ON users (role);

-- [conversations] 索引
CREATE INDEX idx_conv_user_status ON conversations (user_id, status);
CREATE INDEX idx_conv_session ON conversations (session_id);
CREATE INDEX idx_conv_created_at ON conversations (created_at DESC);

-- [messages] 索引
CREATE INDEX idx_msg_conv_created ON messages (conversation_id, created_at);

-- [problem_cards] 索引
CREATE INDEX idx_pc_status ON problem_cards (status);
CREATE INDEX idx_pc_brand_model ON problem_cards (brand, model);
CREATE INDEX idx_pc_created_at ON problem_cards (created_at DESC);

-- [case_entries] 索引
CREATE INDEX idx_ce_brand_active ON case_entries (brand, is_active);

-- [manual_chunks] 索引
CREATE INDEX idx_mc_manual ON manual_chunks (manual_id);
CREATE INDEX idx_mc_manual_chunk ON manual_chunks (manual_id, chunk_index);

-- [sop_drafts] 索引
CREATE INDEX idx_sop_status ON sop_drafts (status);

-- [work_orders] 索引 (V2.0)
CREATE INDEX idx_wo_tech_status ON work_orders (technician_id, status);
CREATE INDEX idx_wo_status_priority ON work_orders (status, priority);

-- [invoices] 索引 (V2.0)
CREATE INDEX idx_inv_wo ON invoices (work_order_id);

-- [reconciliations] 索引 (V2.0)
CREATE INDEX idx_recon_tech_period ON reconciliations (technician_id, period_start);


-- ============================================================================
-- 向量索引 (pgvector HNSW, Cosine Similarity)
-- 參照架構文件 §5.4：向量維度 768, m=16, ef_construction=64
-- ============================================================================

CREATE INDEX idx_case_entry_embedding ON case_entries
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_manual_chunk_embedding ON manual_chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
