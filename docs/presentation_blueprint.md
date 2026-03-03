# 總經理簡報架構藍圖

---

## 簡報結構總覽 (建議 12-15 頁)

| 頁次 | 章節 | 目的 | 停留時間 |
| :--- | :--- | :--- | :--- |
| 1 | 封面 | 建立專業感 | 30s |
| 2 | 現況痛點 | 讓總經理「感受到痛」 | 2min |
| 3 | 解決方案一句話 | 一張圖看懂我們要做什麼 | 1min |
| 4 | 系統架構總覽 | 三個角色 + 平台 + 外部服務的資訊流 | 3min |
| 5 | 技術堆疊金字塔 | 展示技術選型的穩固性 | 1min |
| 6 | AI 三層解決引擎 | 核心競爭力的視覺化 | 2min |
| 7 | 功能模組地圖 | V1.0 / V2.0 交付範圍一覽 | 2min |
| 8 | 交付時程 | 甘特圖，兩階段里程碑 | 2min |
| 9 | 成功指標 | KPI 儀表板式呈現 | 1min |
| 10 | 商業效益 | Before vs After 對比 | 2min |
| 11 | 風險與對策 | 風險矩陣 | 1min |
| 12 | 下一步行動 | 明確請求決策 | 1min |

---

## 逐頁設計規格

---

### P1. 封面

**內容**
- 專案名稱：電子鎖智能客服與派工平台
- 副標題：AI 賦能的售後服務數位轉型
- 日期 / 報告人 / 版本

**圖表**：無，純文字 + 品牌色背景

**ICON**：鎖具圖示 + AI 晶片圖示並列

| 元素 | 建議 ICON | 來源 | Unicode/Class |
| :--- | :--- | :--- | :--- |
| 智慧鎖 | 鎖頭 | Material Icons | `lock` |
| AI | 晶片/大腦 | Material Icons | `psychology` |

---

### P2. 現況痛點

**核心訊息**：目前的流程是碎片化、不可追蹤、不可擴展的

**圖表類型**：**痛點矩陣卡片** (2x2 或 1x4 橫排卡片)

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  ⚠ 知識不可傳承  │  │  ⏱ 診斷效率低落  │  │  📋 派工全靠手動 │  │  💰 帳務不透明   │
│                 │  │                 │  │                 │  │                 │
│ 專家離職=歸零   │  │ 重複問診/誤判高  │  │ LINE+紙本+Excel │  │ 月底對帳爭議多  │
│ 新人培訓數月    │  │ 平均處理 >30min  │  │ 無法追蹤稽核    │  │ 現金流不可控    │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘
```

**ICON 對應**

| 痛點 | ICON | PPT 建議 | Lucide/Heroicons |
| :--- | :--- | :--- | :--- |
| 知識不可傳承 | 腦袋+警告 | `brain` + `alert-triangle` | `Brain`, `AlertTriangle` |
| 診斷效率低落 | 時鐘 | `clock` | `Clock` |
| 派工全靠手動 | 剪貼板 | `clipboard-list` | `ClipboardList` |
| 帳務不透明 | 錢幣+問號 | `currency-dollar` + `question-mark-circle` | `DollarSign`, `HelpCircle` |

---

### P3. 解決方案一句話

**核心訊息**：一個平台，三個角色，從報修到結案全自動

**圖表類型**：**居中大字 + 三角色圖示**

```
            ┌──────────────────────────────┐
            │  AI 驅動的售後服務一站式平台  │
            └──────────────────────────────┘

    👤 消費者            🔧 技師             👔 管理員
    LINE 報修            Web App 接單        儀表板監控
    AI 即時回覆          一鍵接單回報        數據驅動決策
```

**ICON 對應**

| 角色 | ICON | PPT 建議 | Lucide |
| :--- | :--- | :--- | :--- |
| 消費者 | 人像 | `user` | `User` |
| 技師 | 扳手 | `wrench` | `Wrench` |
| 管理員 | 公事包/領帶 | `briefcase` | `Briefcase` |
| LINE 入口 | 對話氣泡 | `message-circle` | `MessageCircle` |
| Web App | 手機 | `smartphone` | `Smartphone` |
| 儀表板 | 長條圖 | `bar-chart-2` | `BarChart2` |

---

### P4. 系統架構總覽 (資訊流)

**核心訊息**：完整的資訊流從報修到結案，12 步閉環

**圖表類型**：直接使用 `executive_architecture_overview.md` 第 2 節的 Mermaid 資訊流圖，匯出為 SVG/PNG 貼入簡報

**簡報呈現建議**：
- 左側放使用者三角色，中間放平台，右側放外部服務
- 用 **動畫分步揭露**：先顯示步驟 1-6 (AI 客服流程)，再顯示 7-12 (派工流程)
- 虛線標註 SOP 自動回饋迴路

**ICON 對應** (與 Mermaid 圖中一致)

| 節點 | Mermaid FA 4 | PPT/Figma 建議 ICON | Lucide |
| :--- | :--- | :--- | :--- |
| 消費者 | `fa:fa-user` | 人像 | `User` |
| 技師 | `fa:fa-wrench` | 扳手 | `Wrench` |
| 管理員 | `fa:fa-user` | 盾牌人像 | `ShieldCheck` |
| LINE Bot AI 客服 | `fa:fa-comments` | 對話氣泡 | `MessageSquare` |
| 技師工作台 | `fa:fa-mobile` | 手機 | `Smartphone` |
| 營運儀表板 | `fa:fa-bar-chart` | 長條圖 | `BarChart2` |
| 問題診斷引擎 | `fa:fa-stethoscope` | 聽診器 | `Stethoscope` |
| 三層解決引擎 | `fa:fa-lightbulb-o` | 燈泡 | `Lightbulb` |
| SOP 自動生成 | `fa:fa-file-text` | 文件+勾 | `FileCheck` |
| 智慧派工引擎 | `fa:fa-cogs` | 齒輪 | `Settings` |
| 報價引擎 | `fa:fa-tags` | 標籤 | `Tags` |
| 帳務模組 | `fa:fa-money` | 錢幣 | `Wallet` |
| PostgreSQL | `fa:fa-database` | 圓柱體 | `Database` |
| pgvector 知識庫 | `fa:fa-book` | 書本+搜尋 | `BookOpen` |
| Redis 快取 | `fa:fa-bolt` | 閃電 | `Zap` |
| LINE API | `fa:fa-commenting` | LINE 官方 Logo | LINE Brand |
| Google Gemini | `fa:fa-cloud` | Google 星形 Logo | Google Brand |

---

### P5. 技術堆疊金字塔

**核心訊息**：穩固的技術基底，成熟且可擴展

**圖表類型**：直接使用 `executive_architecture_overview.md` 第 1 節的堆疊圖，或改為 **梯形金字塔** 手繪風格

**簡報呈現建議**：

```
          ┌─────────────────────────────┐
          │      使用者介面層            │  LINE | Next.js | PWA
          ├─────────────────────────────┤
          │       API 閘道層            │  FastAPI | JWT | OpenAPI
          ├─────────────────────────────┤
          │       AI 服務層             │  LangChain | Gemini 3 Pro
          ├─────────────────────────────┤
          │      業務領域層             │  客服 | 知識庫 | 派工 | 帳務
          ├─────────────────────────────┤
          │      資料存取層             │  SQLAlchemy Async | Alembic
          ├─────────────────────────────┤
          │      基礎設施層             │  PostgreSQL | pgvector | Redis | Docker
          └─────────────────────────────┘
```

- 每層用不同色塊區分 (與 Mermaid classDef 配色一致)
- 右側標註每層的關鍵技術名稱
- 不需要展開細節，總經理看的是「層次分明、選型成熟」

**ICON 對應**

| 層級 | ICON | Lucide |
| :--- | :--- | :--- |
| 使用者介面 | 螢幕 | `Monitor` |
| API 閘道 | 伺服器 | `Server` |
| AI 服務 | 大腦/星火 | `Sparkles` |
| 業務領域 | 拼圖 | `Puzzle` |
| 資料存取 | 雙箭頭 | `ArrowLeftRight` |
| 基礎設施 | 硬碟/容器 | `HardDrive` |

---

### P6. AI 三層解決引擎 (核心亮點頁)

**核心訊息**：問題進來，三道防線，逐層升級

**圖表類型**：**漏斗圖 / 三層瀑布流程**

```
  ┌──────────────────────────────────────────┐
  │  消費者問題進入                           │
  └──────────────┬───────────────────────────┘
                 ▼
  ┌──────────────────────────────────────────┐
  │  L1 - 知識庫精確匹配                     │  ⚡ <1秒
  │  pgvector 語意搜尋，相似度 >= 0.85       │  🎯 預估命中 40%
  └──────────────┬───────────────────────────┘
           未命中 ▼
  ┌──────────────────────────────────────────┐
  │  L2 - AI 推理生成                        │  🤖 <8秒
  │  Gemini 3 Pro RAG，組合知識庫+手冊推理   │  🎯 預估解決 35%
  └──────────────┬───────────────────────────┘
           無解 ▼
  ┌──────────────────────────────────────────┐
  │  L3 - 轉派工                             │  👷 自動建工單
  │  智慧匹配技師，自動派單+報價             │  🎯 剩餘 25%
  └──────────────────────────────────────────┘

       ↻ 成功案例自動回饋知識庫 (SOP 自進化)
```

**ICON 對應**

| 層級 | 含義 | ICON | Lucide |
| :--- | :--- | :--- | :--- |
| L1 | 快速查找 | 閃電+放大鏡 | `Zap`, `Search` |
| L2 | AI 推理 | 大腦/機器人 | `Bot`, `Sparkles` |
| L3 | 人工派工 | 人+扳手 | `UserCog` |
| 自進化迴路 | 知識回饋 | 循環箭頭 | `RefreshCw` |

---

### P7. 功能模組地圖

**核心訊息**：兩階段交付，V1.0 快速上線，V2.0 擴展能力

**圖表類型**：**雙欄模組卡片** (左 V1.0 / 右 V2.0)

```
  V1.0 AI 智能客服 (W1-W17)          V2.0 派工與帳務 (W18-W31)
  ┌─────────────────────────┐        ┌─────────────────────────┐
  │ 💬 LINE Bot AI 客服     │        │ 🔧 智慧派工引擎         │
  │ 🔍 問題診斷引擎         │        │ 💲 報價引擎             │
  │ 💡 三層解決引擎         │        │ 📊 帳務結算模組         │
  │ 📚 知識庫管理           │        │ 📱 技師工作台 PWA       │
  │ 📝 SOP 自動生成         │        │ 🖥  增強管理後台        │
  │ ⚙  管理後台 (基礎版)    │        │                         │
  └─────────────────────────┘        └─────────────────────────┘

  共用基礎：身分認證 | 通知服務 | 可觀測性
```

**ICON 對應**

| 模組 | PPT ICON | Lucide |
| :--- | :--- | :--- |
| LINE Bot AI 客服 | 對話氣泡 | `MessageSquare` |
| 問題診斷引擎 | 聽診器 | `Stethoscope` |
| 三層解決引擎 | 燈泡 | `Lightbulb` |
| 知識庫管理 | 書本 | `BookOpen` |
| SOP 自動生成 | 文件+筆 | `FileEdit` |
| 管理後台 | 齒輪儀表板 | `LayoutDashboard` |
| 智慧派工 | 齒輪組 | `Settings` |
| 報價引擎 | 標籤/價格 | `Tags` |
| 帳務結算 | 錢包 | `Wallet` |
| 技師工作台 | 手機 | `Smartphone` |
| 增強管理後台 | 多螢幕 | `Monitor` |
| 身分認證 | 鎖頭 | `Lock` |
| 通知服務 | 鈴鐺 | `Bell` |
| 可觀測性 | 活動監控 | `Activity` |

---

### P8. 交付時程

**核心訊息**：31 週，兩階段，關鍵里程碑清晰

**圖表類型**：**甘特圖 (橫向時間軸)**

```
W1──────W2──W3─────────W7──W8──────────W12──W13────W15──W16──W17
│ Phase 0  │  Phase 1    │   Phase 2     │  Phase 3   │ Phase 4│
│ 架構設計 │  AI MVP     │  三層引擎+KB  │  UAT 驗收  │ V1上線 │
                                                         ▼
W18────W19──W20────────W24──W25────────W29──W30────W31
│ Phase 5  │  Phase 6    │   Phase 7     │  Phase 8   │
│ V2設計   │  派工 MVP   │  帳務+整合    │  V2上線    │
```

**ICON 對應**

| 里程碑 | ICON | Lucide |
| :--- | :--- | :--- |
| 架構設計 | 藍圖 | `FileCode` |
| MVP | 火箭 | `Rocket` |
| UAT 驗收 | 勾勾盾牌 | `ShieldCheck` |
| 正式上線 | 旗幟 | `Flag` |

---

### P9. 成功指標 (KPI Dashboard)

**核心訊息**：量化目標，可驗證的成功定義

**圖表類型**：**儀表板卡片** (3x2 網格，每格一個 KPI)

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  🎯 >= 80%   │  │  ⚡ < 5 秒    │  │  🤖 >= 40%   │
│  AI 回答準確率│  │  AI 首次回應  │  │  自助解決率   │
└──────────────┘  └──────────────┘  └──────────────┘
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  👥 >= 50人   │  │  ✅ >= 99.5%  │  │  🔄 E2E 全通 │
│  V1.0 併發數 │  │  系統可用率   │  │  報修→結案   │
└──────────────┘  └──────────────┘  └──────────────┘
```

**ICON 對應**

| KPI | ICON | Lucide |
| :--- | :--- | :--- |
| AI 準確率 | 靶心 | `Target` |
| 回應速度 | 閃電 | `Zap` |
| 自助解決率 | 機器人 | `Bot` |
| 併發數 | 多人 | `Users` |
| 可用率 | 勾勾 | `CheckCircle` |
| E2E 流程 | 循環 | `RefreshCw` |

---

### P10. 商業效益 (Before vs After)

**核心訊息**：數位轉型帶來的具體改變

**圖表類型**：**左右對比表** (紅色 Before / 綠色 After)

```
        ❌ Before (現況)           →          ✅ After (平台上線後)
  ┌─────────────────────────┐         ┌─────────────────────────┐
  │ 客服靠人工逐一問診      │   →     │ AI 7x24 自動處理 40%    │
  │ 知識存在技師腦中        │   →     │ 知識庫數位化可傳承      │
  │ LINE+紙本+Excel 派工    │   →     │ 系統自動匹配派單        │
  │ 月底手動對帳常有爭議    │   →     │ 即時帳務透明可稽核      │
  │ 決策憑直覺              │   →     │ 數據儀表板輔助決策      │
  └─────────────────────────┘         └─────────────────────────┘
```

**ICON 對應**

| 面向 | Before ICON | After ICON | Lucide |
| :--- | :--- | :--- | :--- |
| 客服 | 電話 | 機器人 | `Phone` → `Bot` |
| 知識 | 腦袋 | 資料庫 | `Brain` → `Database` |
| 派工 | 文件 | 齒輪自動 | `FileText` → `Settings` |
| 帳務 | 計算機 | 勾勾帳本 | `Calculator` → `FileCheck` |
| 決策 | 問號 | 圖表 | `HelpCircle` → `BarChart2` |

---

### P11. 風險與對策

**核心訊息**：已識別關鍵風險，每個都有具體對策

**圖表類型**：**風險矩陣** (影響 x 機率) 或 **風險卡片列表**

```
  風險                    機率    影響    對策
  ┌───────────────────────────────────────────────────────┐
  │ 🔴 AI 準確率未達標    中      高      50 題標準測試集  │
  │                                      持續微調 Prompt  │
  ├───────────────────────────────────────────────────────┤
  │ 🟡 甲方資料提供延遲   中      中      Phase 0 預先收集 │
  │                                      Mock 資料先行開發 │
  ├───────────────────────────────────────────────────────┤
  │ 🟡 Gemini API 變動    低      中高    LLM Gateway 抽象 │
  │                                      可隨時切換模型    │
  ├───────────────────────────────────────────────────────┤
  │ 🟢 用戶接受度低       低      中      漸進式導入       │
  │                                      保留人工客服後路  │
  └───────────────────────────────────────────────────────┘
```

**ICON 對應**

| 風險等級 | ICON | Lucide |
| :--- | :--- | :--- |
| 高風險 | 紅色圓形 | `AlertOctagon` (紅) |
| 中風險 | 黃色三角 | `AlertTriangle` (黃) |
| 低風險 | 綠色圓形 | `CheckCircle` (綠) |
| 對策 | 盾牌 | `Shield` |

---

### P12. 下一步行動

**核心訊息**：請求核准，明確下一步

**圖表類型**：**行動清單** (3-4 項，帶負責人與時間)

```
  請求決策：
  ┌────┬──────────────────────────────┬─────────┬──────────┐
  │ #  │ 行動項目                     │ 負責人   │ 期限     │
  ├────┼──────────────────────────────┼─────────┼──────────┤
  │ 1  │ 核准專案啟動與預算           │ 總經理   │ 本週     │
  │ 2  │ 提供 LINE 官方帳號與歷史資料 │ 甲方 PM  │ W1       │
  │ 3  │ 確認 50 題標準測試集         │ 領域專家 │ W2       │
  │ 4  │ Phase 0 架構設計啟動         │ 開發團隊 │ W1       │
  └────┴──────────────────────────────┴─────────┴──────────┘
```

**ICON 對應**

| 項目 | ICON | Lucide |
| :--- | :--- | :--- |
| 核准 | 勾勾 | `CheckSquare` |
| 資料提供 | 上傳 | `Upload` |
| 測試集 | 列表勾勾 | `ListChecks` |
| 啟動 | 火箭 | `Rocket` |

---

## ICON 統一對照總表

簡報製作時，所有 ICON 建議統一使用同一套圖示庫。以下為三套主流庫的完整對照：

| 語意 | Mermaid (FA 4) | Lucide (推薦) | Material Icons | Heroicons |
| :--- | :--- | :--- | :--- | :--- |
| 使用者/消費者 | `fa-user` | `User` | `person` | `UserIcon` |
| 技師 | `fa-wrench` | `Wrench` | `build` | `WrenchScrewdriverIcon` |
| 管理員 | `fa-user` | `Briefcase` | `admin_panel_settings` | `BriefcaseIcon` |
| 對話/客服 | `fa-comments` | `MessageSquare` | `chat` | `ChatBubbleLeftRightIcon` |
| 手機/App | `fa-mobile` | `Smartphone` | `phone_iphone` | `DevicePhoneMobileIcon` |
| 儀表板 | `fa-bar-chart` | `BarChart2` | `bar_chart` | `ChartBarIcon` |
| 診斷 | `fa-stethoscope` | `Stethoscope` | `medical_services` | - |
| 燈泡/解決 | `fa-lightbulb-o` | `Lightbulb` | `lightbulb` | `LightBulbIcon` |
| 文件/SOP | `fa-file-text` | `FileText` | `description` | `DocumentTextIcon` |
| 齒輪/派工 | `fa-cogs` | `Settings` | `settings` | `CogIcon` |
| 標籤/報價 | `fa-tags` | `Tags` | `sell` | `TagIcon` |
| 錢/帳務 | `fa-money` | `Wallet` | `payments` | `CurrencyDollarIcon` |
| 資料庫 | `fa-database` | `Database` | `storage` | `CircleStackIcon` |
| 知識庫/書本 | `fa-book` | `BookOpen` | `menu_book` | `BookOpenIcon` |
| 快取/閃電 | `fa-bolt` | `Zap` | `bolt` | `BoltIcon` |
| 雲端/API | `fa-cloud` | `Cloud` | `cloud` | `CloudIcon` |
| 對話泡泡 | `fa-commenting` | `MessageCircle` | `comment` | `ChatBubbleLeftIcon` |
| AI/大腦 | - | `Sparkles` | `psychology` | `SparklesIcon` |
| 搜尋 | `fa-search` | `Search` | `search` | `MagnifyingGlassIcon` |
| 鎖頭/安全 | `fa-lock` | `Lock` | `lock` | `LockClosedIcon` |
| 盾牌/防護 | `fa-shield` | `Shield` | `shield` | `ShieldCheckIcon` |
| 火箭/啟動 | - | `Rocket` | `rocket_launch` | `RocketLaunchIcon` |
| 旗幟/里程碑 | `fa-flag` | `Flag` | `flag` | `FlagIcon` |
| 警告 | `fa-exclamation-triangle` | `AlertTriangle` | `warning` | `ExclamationTriangleIcon` |
| 勾勾/完成 | `fa-check` | `CheckCircle` | `check_circle` | `CheckCircleIcon` |
| 循環/回饋 | - | `RefreshCw` | `sync` | `ArrowPathIcon` |
| 靶心/目標 | `fa-bullseye` | `Target` | `gps_fixed` | - |
| 鈴鐺/通知 | `fa-bell` | `Bell` | `notifications` | `BellIcon` |
| 活動/監控 | - | `Activity` | `monitoring` | - |

---

## 配色方案

與 Mermaid 圖一致的色票，建議簡報統一使用：

| 區域 | 背景色 | 邊框色 | 用途 |
| :--- | :--- | :--- | :--- |
| 使用者/介面 | `#E3F2FD` | `#1565C0` | 使用者相關元素 |
| AI 引擎 | `#EDE7F6` | `#4527A0` | AI/智能相關元素 |
| 業務引擎 | `#FFF3E0` | `#E65100` | 業務邏輯相關元素 |
| 資料層 | `#E8F5E9` | `#2E7D32` | 資料庫/知識庫 |
| 基礎設施 | `#ECEFF1` | `#37474F` | 底層基礎設施 |
| 警告/風險 | `#FFF8E1` | `#F57F17` | 風險/注意事項 |
| 正向/成功 | `#E8F5E9` | `#2E7D32` | KPI 達標/效益 |
| 負面/痛點 | `#FFEBEE` | `#C62828` | 痛點/問題 |

---

## 簡報工具建議

| 工具 | 用途 |
| :--- | :--- |
| **Mermaid Live Editor** → 匯出 SVG | 架構圖 (P4) 和堆疊圖 (P5) |
| **Lucide Icons** (lucide.dev) | 統一 ICON 來源，SVG 可直接貼入 PPT/Figma |
| **Figma / Canva** | 簡報排版，可直接使用上述色票 |
| **PowerPoint** | 最終交付格式，ICON 用 SVG 插入確保縮放不失真 |

---
