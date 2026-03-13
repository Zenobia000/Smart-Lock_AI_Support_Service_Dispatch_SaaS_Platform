# Agent 人格與提示詞調整指南

本專案將 Prompt 全面外置化，以 Markdown 檔案管理，旨在實現「設定即開發」。

---

## 1. 檔案結構與對應

所有 Prompt 存放於 `agents/prompts/` 目錄：

*   `router.md`: **中央調度員**。負責解析意圖並指派 Agent。
*   `product_expert.md`: **產品專家**。
*   `troubleshooter.md`: **故障排除專家**。
*   `order_clerk.md`: **訂單查詢專員**。
*   `web_researcher.md`: **網路搜尋助手**。
*   `summarize_messages.md`: **記憶壓縮器**。負責將對話精煉為摘要。
*   `merge_answers.md`: **回覆合併器**。當多個意圖同時觸發時，負責將多段回答融合成一段自然文字。
*   `update_profile.md`: **輪廓觀察員**。負責從對話中學習使用者的背景。

---

## 2. 核心模板變數 (Template Variables)

在修改 `.md` 檔案時，可以使用以下變數，系統會自動注入：

| 變數 | 說明 | 注入來源 |
|------|------|---------|
| `{domain}` | 業務範疇描述 | `config.toml [system].domain` |
| `{user_profile}` | 當前使用者輪廓文字 | `user_profiles/*.md` |
| `{slots_section}` | 必填資訊填補指示 | `config.toml [required_slots]` |
| `{intent_list}` | 可選意圖清單 | `config.toml [[intents]]` |
| `{existing_summary}`| 現有的對話摘要 | `state["summary"]` |

---

## 3. 調整指南：避免失能

### 3.1 關鍵指令：工具優先原則
所有 Agent Prompt 必須包含以下段落，否則 LLM 可能會因為已經讀到了 `[前情提要]` 而跳過工具檢索：
> 「你必須使用工具來檢索資料，不可直接憑記憶回答。對話摘要（[前情提要]）僅供理解上下文，不可取代工具檢索——每次回覆前都必須先呼叫工具。」

### 3.2 摘要策略調整 (`summarize_messages.md`)
摘要節點的目的是「精煉而非刪除」。調整時應確保 LLM 始終追蹤以下資訊：
*   **設備現狀**（品牌、型號、當前狀況）。
*   **議題狀態**（已解決、處理中、待追蹤）。
*   **已告知使用者的資訊**（避免重複建議）。

### 3.3 回覆合併策略 (`merge_answers.md`)
當使用者同時問「規格」與「訂單」時：
*   不要分開回覆兩次「您好」。
*   應以結構化方式（如分段、標點）將兩個 Agent 的回報結果融合成一篇專業的應對。

### 3.4 純文字格式規範（LINE 平台適配）
LINE 平台不支援 Markdown 渲染，因此所有面向使用者的 Agent Prompt 必須包含以下規則：
> 「回覆格式必須是純文字，禁止使用任何 Markdown 語法（如 ** 粗體、# 標題、[]() 連結、` 程式碼）。排版請用換行與數字編號（1. 2. 3.）即可。」

此規則適用於：`product_expert.md`、`troubleshooter.md`、`order_clerk.md`、`web_researcher.md`、`merge_answers.md`。

不適用於：`router.md`（輸出為意圖名稱）、`summarize_messages.md`（內部摘要）、`update_profile.md`（輸出為 Markdown 格式的 user profile）。

作為結尾防線，`graph/nodes.py` 的 `post_process` 節點會透過 `_strip_markdown()` 函數以 regex 清洗殘留的 Markdown 標記，確保最終回覆為純文字。

---

## 4. 人格設定 (Persona)

*   **語氣**：專業、親切、簡潔。
*   **禁忌**：嚴禁提及「我只是一個 AI」、「我的知識庫更新於...」。一律以「電子鎖專屬客服」的身分自居。
*   **安全邊界**：涉及門鎖受損或安全隱患時，語氣需變得嚴肅並立即主動引導轉接真人客服。
