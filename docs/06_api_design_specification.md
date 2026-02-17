# API 設計規範 - 電子鎖智能客服與派工平台

---

**文件版本:** `v1.0`

**最後更新:** `2026-02-17`

**主要作者:** 開發團隊

**狀態:** 已批准 (Approved)

**相關文檔:** `docs/05_architecture_and_design_document.md`

---

## 目錄

1.  [引言](#1-引言)
2.  [設計原則與約定](#2-設計原則與約定)
3.  [認證與授權](#3-認證與授權)
4.  [通用 API 行為](#4-通用-api-行為)
5.  [錯誤處理](#5-錯誤處理)
6.  [安全性考量](#6-安全性考量)
7.  [V1.0 API 端點詳述](#7-v10-api-端點詳述)
8.  [V2.0 API 端點詳述](#8-v20-api-端點詳述)
9.  [資料模型/Schema 定義](#9-資料模型schema-定義)
10. [API 生命週期與版本控制](#10-api-生命週期與版本控制)
11. [附錄](#11-附錄)

---

## 1. 引言

### 1.1 目的

本文件為「電子鎖智能客服與派工 SaaS 平台」的所有 API 消費者與實現者提供統一、明確的接口契約。涵蓋 V1.0（AI 客服與知識庫）及 V2.0（派工與計價）全部端點規範。

### 1.2 目標讀者

- 前端開發者（Admin Panel、技師 App）
- 後端開發者（FastAPI 實現者）
- LINE Bot 整合開發者
- QA 測試工程師
- 技術文件撰寫者

### 1.3 快速入門

**第 1 步：取得管理員帳號並登入**

```bash
curl -X POST https://api.smartlock-saas.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin@example.com",
    "password": "your_password"
  }'
```

**預期回應：**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "dGhpcyBpcyBhIHJlZnJl..."
}
```

**第 2 步：使用 Token 呼叫 API**

```bash
curl -X GET https://api.smartlock-saas.com/api/v1/conversations \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Accept: application/json"
```

---

## 2. 設計原則與約定

### 2.1 API 風格

- **風格：** RESTful
- **核心原則：** 資源導向、無狀態、標準 HTTP 方法語意。

| HTTP Method | 語意 | 冪等性 |
|:---|:---|:---|
| `GET` | 讀取資源 | Yes |
| `POST` | 建立資源 / 觸發動作 | No |
| `PUT` | 完整替換資源 | Yes |
| `PATCH` | 部分更新資源 | No |
| `DELETE` | 刪除資源 | Yes |

### 2.2 基本 URL

| 環境 | Base URL |
|:---|:---|
| Production | `https://api.smartlock-saas.com/api/v1` |
| Staging | `https://staging-api.smartlock-saas.com/api/v1` |
| Development | `http://localhost:8000/api/v1` |

### 2.3 請求與回應格式

- 所有請求與回應皆使用 `application/json`（UTF-8）。
- 檔案上傳端點使用 `multipart/form-data`。

### 2.4 標準 HTTP Headers

**所有請求：**

| Header | 說明 | 必填 |
|:---|:---|:---|
| `Authorization` | `Bearer <access_token>` | 視端點而定 |
| `Content-Type` | `application/json` | POST/PUT/PATCH |
| `Accept` | `application/json` | 建議 |
| `X-Request-ID` | UUID，用於請求追蹤 | 選填 |
| `Idempotency-Key` | UUID，用於冪等性保證 | 選填 |

**所有回應：**

| Header | 說明 |
|:---|:---|
| `X-Request-ID` | 請求追蹤 ID |
| `RateLimit-Limit` | 速率上限 |
| `RateLimit-Remaining` | 剩餘配額 |
| `RateLimit-Reset` | 重置時間（Unix timestamp） |

### 2.5 命名約定

- **資源路徑：** 小寫，連字符分隔，名詞複數（e.g., `/problem-cards`, `/work-orders`）
- **JSON 欄位 & 查詢參數：** `snake_case`（e.g., `created_at`, `line_user_id`）

### 2.6 日期與時間格式

所有日期時間使用 ISO 8601 格式，UTC 時區：`2026-02-17T10:30:00Z`

---

## 3. 認證與授權

### 3.1 Admin Panel：JWT Bearer Token

管理後台使用 JWT Token 認證。

- **取得方式：** `POST /api/v1/auth/login`
- **Token 類型：** Bearer
- **Access Token 有效期：** 1 小時
- **Refresh Token 有效期：** 7 天

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### 3.2 LINE Bot：LINE Signature Verification

LINE Webhook 端點不使用 JWT，改以 LINE Platform 的 `X-Line-Signature` Header 驗證請求真偽。伺服器以 Channel Secret 計算 HMAC-SHA256 並比對簽名。

### 3.3 Technician App (V2.0)：JWT Bearer Token

技師端 App 使用獨立的 JWT Token 認證流程。

- **取得方式：** `POST /api/v1/technicians/login`
- **Token 載荷包含：** `technician_id`, `role: "technician"`
- **有效期：** 同 Admin Panel

### 3.4 Role-Based Access Control

| 角色 | 說明 | 可存取資源 |
|:---|:---|:---|
| `admin` | 系統管理員 | 全部資源 |
| `reviewer` | SOP 審核員 | Conversations, ProblemCards, SOPDrafts, Knowledge Base |
| `technician` | 現場技師 (V2.0) | WorkOrders (自身), Technicians/me |

---

## 4. 通用 API 行為

### 4.1 分頁（Cursor-based）

所有列表端點使用 cursor-based 分頁。

**查詢參數：**

| 參數 | 類型 | 預設 | 說明 |
|:---|:---|:---|:---|
| `limit` | integer | 20 | 每頁筆數（最大 100） |
| `cursor` | string | null | 上一頁回傳的 `next_cursor` |

**回應結構：**

```json
{
  "data": [],
  "pagination": {
    "next_cursor": "eyJpZCI6MTAwfQ==",
    "has_more": true,
    "total_count": 256
  }
}
```

### 4.2 排序

**查詢參數：** `sort_by`

- 升序（預設）：`sort_by=created_at`
- 降序：`sort_by=-created_at`

### 4.3 過濾

直接使用欄位名作為查詢參數。

```
GET /api/v1/problem-cards?status=pending&brand=Yale
```

### 4.4 冪等性

非 GET 請求可攜帶 `Idempotency-Key` Header。伺服器在 24 小時內對相同 key 的重複請求回傳第一次的結果。

---

## 5. 錯誤處理

### 5.1 標準錯誤格式

```json
{
  "error": {
    "type": "validation_error",
    "code": "parameter_invalid",
    "message": "brand is required and cannot be empty.",
    "param": "brand",
    "request_id": "req_abc123"
  }
}
```

### 5.2 HTTP 狀態碼

| 狀態碼 | 說明 | 使用情境 |
|:---|:---|:---|
| `200` | OK | 成功讀取或更新 |
| `201` | Created | 成功建立資源 |
| `204` | No Content | 成功刪除 |
| `400` | Bad Request | 參數驗證失敗 |
| `401` | Unauthorized | Token 無效或過期 |
| `403` | Forbidden | 權限不足 |
| `404` | Not Found | 資源不存在 |
| `409` | Conflict | 資源衝突 |
| `422` | Unprocessable Entity | 語意錯誤 |
| `429` | Too Many Requests | 超過速率限制 |
| `500` | Internal Server Error | 伺服器內部錯誤 |

### 5.3 錯誤碼字典

| error.code | HTTP 狀態碼 | 描述 |
|:---|:---|:---|
| `parameter_missing` | 400 | 缺少必要參數 |
| `parameter_invalid` | 400 | 參數格式或值不合法 |
| `authentication_failed` | 401 | 認證失敗 |
| `token_expired` | 401 | Token 已過期 |
| `permission_denied` | 403 | 無此操作權限 |
| `resource_not_found` | 404 | 資源不存在 |
| `resource_conflict` | 409 | 資源狀態衝突 |
| `rate_limit_exceeded` | 429 | 超出速率限制 |
| `line_signature_invalid` | 401 | LINE Webhook 簽名驗證失敗 |
| `resolution_failed` | 500 | 解決方案引擎執行失敗 |
| `dispatch_no_match` | 422 | 找不到可用技師 |
| `work_order_state_invalid` | 409 | 工單狀態不允許此操作 |
| `vector_search_failed` | 500 | 向量搜尋引擎異常 |
| `file_too_large` | 400 | 上傳檔案超過大小限制 |
| `unsupported_file_type` | 400 | 不支援的檔案類型 |

---

## 6. 安全性考量

### 6.1 TLS

所有 API 端點強制使用 HTTPS（TLS 1.2+）。HTTP 請求一律回傳 `301` 導向 HTTPS。

### 6.2 Rate Limiting

| 端點類型 | 限制 |
|:---|:---|
| LINE Webhook | 1000 req/min |
| Auth 端點 | 10 req/min per IP |
| 一般 API | 200 req/min per token |
| Vector Search | 30 req/min per token |

### 6.3 LINE Webhook Signature Verification

```python
import hashlib
import hmac
import base64

def verify_line_signature(body: bytes, signature: str, channel_secret: str) -> bool:
    hash = hmac.new(
        channel_secret.encode("utf-8"), body, hashlib.sha256
    ).digest()
    return hmac.compare_digest(signature, base64.b64encode(hash).decode("utf-8"))
```

### 6.4 Prompt Injection Protection

- 使用者輸入在送入 LLM 前，先經過 sanitization 處理。
- System prompt 與 user input 嚴格分離。
- 設定 output guardrails 防止 LLM 洩漏系統提示詞。
- 所有 LLM 回應經過後處理過濾。

---

## 7. V1.0 API 端點詳述

### 7.1 LINE Webhook

#### `POST /api/v1/webhook/line`

接收 LINE Platform 推送的訊息事件（文字、圖片）。

- **授權：** LINE Signature Verification（`X-Line-Signature` Header）
- **觸發流程：** 接收訊息 -> 建立/更新 Conversation -> 觸發 Resolution Engine

**Request Headers：**

| Header | 說明 |
|:---|:---|
| `X-Line-Signature` | LINE Platform 產生的 HMAC-SHA256 簽名 |
| `Content-Type` | `application/json` |

**Request Body（由 LINE Platform 送出）：**

```json
{
  "destination": "Uxxxxxxxxxxxxx",
  "events": [
    {
      "type": "message",
      "message": {
        "type": "text",
        "id": "46827381744",
        "text": "我的 Yale 電子鎖打不開，型號 YDM4109"
      },
      "source": {
        "type": "user",
        "userId": "U1234567890abcdef"
      },
      "replyToken": "nHuyWiB7yP5Zw52FIkcQobQuGDXCTA",
      "timestamp": 1708171800000
    }
  ]
}
```

**Success Response（200 OK）：**

```json
{
  "status": "ok",
  "events_processed": 1
}
```

**Error Responses：**

| 狀態碼 | 情境 |
|:---|:---|
| `401` | LINE 簽名驗證失敗 |
| `500` | 內部處理錯誤 |

---

### 7.2 Conversations

#### `GET /api/v1/conversations`

取得對話列表。

- **授權：** `admin`, `reviewer`
- **分頁：** 支援
- **過濾參數：** `status` (`active`, `resolved`, `escalated`), `line_user_id`, `created_after`, `created_before`
- **排序：** `sort_by` (`-created_at` 預設)

**Request：**

```bash
curl -X GET "https://api.smartlock-saas.com/api/v1/conversations?status=active&limit=10" \
  -H "Authorization: Bearer {token}"
```

**Success Response（200 OK）：**

```json
{
  "data": [
    {
      "id": "conv_01HQXK5V8N3M2P4R6T",
      "line_user_id": "U1234567890abcdef",
      "status": "active",
      "problem_card_id": "pc_01HQXK6A9B7C3D5E8F",
      "message_count": 5,
      "created_at": "2026-02-17T08:30:00Z",
      "updated_at": "2026-02-17T09:15:00Z"
    }
  ],
  "pagination": {
    "next_cursor": "eyJpZCI6ImNvbnZfMDEi",
    "has_more": true,
    "total_count": 48
  }
}
```

---

#### `GET /api/v1/conversations/{id}`

取得單一對話詳情。

- **授權：** `admin`, `reviewer`

**Request：**

```bash
curl -X GET "https://api.smartlock-saas.com/api/v1/conversations/conv_01HQXK5V8N3M2P4R6T" \
  -H "Authorization: Bearer {token}"
```

**Success Response（200 OK）：**

```json
{
  "id": "conv_01HQXK5V8N3M2P4R6T",
  "line_user_id": "U1234567890abcdef",
  "status": "active",
  "problem_card_id": "pc_01HQXK6A9B7C3D5E8F",
  "messages": [
    {
      "role": "user",
      "content": "我的 Yale 電子鎖打不開，型號 YDM4109",
      "timestamp": "2026-02-17T08:30:00Z"
    },
    {
      "role": "assistant",
      "content": "了解，請問您的鎖是完全沒有反應，還是有嗶聲但無法開啟？",
      "timestamp": "2026-02-17T08:30:02Z"
    }
  ],
  "message_count": 5,
  "created_at": "2026-02-17T08:30:00Z",
  "updated_at": "2026-02-17T09:15:00Z"
}
```

**Error Responses：**

| 狀態碼 | error.code | 情境 |
|:---|:---|:---|
| `404` | `resource_not_found` | 對話不存在 |

---

#### `GET /api/v1/conversations/{id}/messages`

取得對話的訊息歷程（支援分頁）。

- **授權：** `admin`, `reviewer`
- **分頁：** 支援
- **排序：** `sort_by` (`created_at` 預設，時間正序)

**Request：**

```bash
curl -X GET "https://api.smartlock-saas.com/api/v1/conversations/conv_01HQXK5V8N3M2P4R6T/messages?limit=50" \
  -H "Authorization: Bearer {token}"
```

**Success Response（200 OK）：**

```json
{
  "data": [
    {
      "id": "msg_01HQXK7B2C4D6E8F0G",
      "role": "user",
      "type": "text",
      "content": "我的 Yale 電子鎖打不開，型號 YDM4109",
      "timestamp": "2026-02-17T08:30:00Z"
    },
    {
      "id": "msg_01HQXK7C3D5E7F9G1H",
      "role": "assistant",
      "type": "text",
      "content": "了解，請問您的鎖是完全沒有反應，還是有嗶聲但無法開啟？",
      "timestamp": "2026-02-17T08:30:02Z"
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_more": false,
    "total_count": 5
  }
}
```

---

### 7.3 ProblemCards

#### `POST /api/v1/problem-cards`

建立診斷問題卡（通常由系統自動建立，也可手動建立）。

- **授權：** `admin`

**Request Body：**

```json
{
  "conversation_id": "conv_01HQXK5V8N3M2P4R6T",
  "brand": "Yale",
  "model": "YDM4109",
  "location": "台北市大安區忠孝東路四段100號12樓",
  "door_status": "locked_out",
  "network_status": "offline",
  "symptoms": ["no_response", "battery_low_indicator"],
  "intent": "unlock_request"
}
```

**Success Response（201 Created）：**

```json
{
  "id": "pc_01HQXK6A9B7C3D5E8F",
  "conversation_id": "conv_01HQXK5V8N3M2P4R6T",
  "brand": "Yale",
  "model": "YDM4109",
  "location": "台北市大安區忠孝東路四段100號12樓",
  "door_status": "locked_out",
  "network_status": "offline",
  "symptoms": ["no_response", "battery_low_indicator"],
  "intent": "unlock_request",
  "status": "open",
  "created_at": "2026-02-17T08:35:00Z"
}
```

**Error Responses：**

| 狀態碼 | error.code | 情境 |
|:---|:---|:---|
| `400` | `parameter_missing` | 缺少必要欄位 |
| `400` | `parameter_invalid` | 欄位值不合法 |

---

#### `GET /api/v1/problem-cards`

取得問題卡列表。

- **授權：** `admin`, `reviewer`
- **分頁：** 支援
- **過濾參數：** `status` (`open`, `in_progress`, `resolved`, `escalated`), `brand`, `model`, `intent`, `created_after`, `created_before`
- **排序：** `sort_by` (`-created_at` 預設)

**Request：**

```bash
curl -X GET "https://api.smartlock-saas.com/api/v1/problem-cards?brand=Yale&status=open&limit=20" \
  -H "Authorization: Bearer {token}"
```

**Success Response（200 OK）：**

```json
{
  "data": [
    {
      "id": "pc_01HQXK6A9B7C3D5E8F",
      "conversation_id": "conv_01HQXK5V8N3M2P4R6T",
      "brand": "Yale",
      "model": "YDM4109",
      "location": "台北市大安區忠孝東路四段100號12樓",
      "door_status": "locked_out",
      "network_status": "offline",
      "symptoms": ["no_response", "battery_low_indicator"],
      "intent": "unlock_request",
      "status": "open",
      "created_at": "2026-02-17T08:35:00Z"
    }
  ],
  "pagination": {
    "next_cursor": "eyJpZCI6InBjXzAyIn0=",
    "has_more": false,
    "total_count": 1
  }
}
```

---

#### `GET /api/v1/problem-cards/{id}`

取得單一問題卡詳情。

- **授權：** `admin`, `reviewer`

**Request：**

```bash
curl -X GET "https://api.smartlock-saas.com/api/v1/problem-cards/pc_01HQXK6A9B7C3D5E8F" \
  -H "Authorization: Bearer {token}"
```

**Success Response（200 OK）：**

```json
{
  "id": "pc_01HQXK6A9B7C3D5E8F",
  "conversation_id": "conv_01HQXK5V8N3M2P4R6T",
  "brand": "Yale",
  "model": "YDM4109",
  "location": "台北市大安區忠孝東路四段100號12樓",
  "door_status": "locked_out",
  "network_status": "offline",
  "symptoms": ["no_response", "battery_low_indicator"],
  "intent": "unlock_request",
  "status": "open",
  "created_at": "2026-02-17T08:35:00Z"
}
```

**Error Responses：**

| 狀態碼 | error.code | 情境 |
|:---|:---|:---|
| `404` | `resource_not_found` | 問題卡不存在 |

---

#### `PATCH /api/v1/problem-cards/{id}`

部分更新問題卡（例如補充症狀、更新狀態）。

- **授權：** `admin`

**Request Body：**

```json
{
  "symptoms": ["no_response", "battery_low_indicator", "keypad_unresponsive"],
  "status": "in_progress"
}
```

**Success Response（200 OK）：**

```json
{
  "id": "pc_01HQXK6A9B7C3D5E8F",
  "conversation_id": "conv_01HQXK5V8N3M2P4R6T",
  "brand": "Yale",
  "model": "YDM4109",
  "location": "台北市大安區忠孝東路四段100號12樓",
  "door_status": "locked_out",
  "network_status": "offline",
  "symptoms": ["no_response", "battery_low_indicator", "keypad_unresponsive"],
  "intent": "unlock_request",
  "status": "in_progress",
  "created_at": "2026-02-17T08:35:00Z"
}
```

---

#### `GET /api/v1/problem-cards/{id}/export`

匯出問題卡為結構化格式（用於派工單或報表）。

- **授權：** `admin`
- **查詢參數：** `format` (`json` 預設, `pdf`)

**Request：**

```bash
curl -X GET "https://api.smartlock-saas.com/api/v1/problem-cards/pc_01HQXK6A9B7C3D5E8F/export?format=json" \
  -H "Authorization: Bearer {token}"
```

**Success Response（200 OK）：**

```json
{
  "problem_card": {
    "id": "pc_01HQXK6A9B7C3D5E8F",
    "brand": "Yale",
    "model": "YDM4109",
    "location": "台北市大安區忠孝東路四段100號12樓",
    "door_status": "locked_out",
    "network_status": "offline",
    "symptoms": ["no_response", "battery_low_indicator", "keypad_unresponsive"],
    "intent": "unlock_request"
  },
  "conversation_summary": "用戶反映 Yale YDM4109 電子鎖無法開啟，鍵盤無反應，疑似電池耗盡。",
  "suggested_resolution": "更換電池，若仍無反應則需現場檢修馬達模組。",
  "exported_at": "2026-02-17T10:00:00Z"
}
```

---

### 7.4 Knowledge Base - Case Entries

#### `POST /api/v1/knowledge-base/cases`

新增案例至知識庫。系統會自動產生 embedding 向量。

- **授權：** `admin`, `reviewer`

**Request Body：**

```json
{
  "title": "Yale YDM4109 電池耗盡無法開鎖",
  "problem_description": "用戶反映 Yale YDM4109 鍵盤完全無反應，無法輸入密碼開鎖。",
  "solution": "1. 使用 9V 電池緊急供電（觸點位於鎖體下方）\n2. 輸入密碼開鎖\n3. 更換內部 4 顆 AA 電池\n4. 重新測試鍵盤功能",
  "brand": "Yale",
  "model": "YDM4109",
  "tags": ["battery", "lockout", "keypad"]
}
```

**Success Response（201 Created）：**

```json
{
  "id": "case_01HQXM3A4B5C6D7E8F",
  "title": "Yale YDM4109 電池耗盡無法開鎖",
  "problem_description": "用戶反映 Yale YDM4109 鍵盤完全無反應，無法輸入密碼開鎖。",
  "solution": "1. 使用 9V 電池緊急供電（觸點位於鎖體下方）\n2. 輸入密碼開鎖\n3. 更換內部 4 顆 AA 電池\n4. 重新測試鍵盤功能",
  "brand": "Yale",
  "model": "YDM4109",
  "tags": ["battery", "lockout", "keypad"],
  "verified": false,
  "embedding_status": "processing",
  "created_at": "2026-02-17T09:00:00Z"
}
```

---

#### `GET /api/v1/knowledge-base/cases`

取得案例列表。

- **授權：** `admin`, `reviewer`
- **分頁：** 支援
- **過濾參數：** `brand`, `model`, `verified` (`true`/`false`), `tags`
- **排序：** `sort_by` (`-created_at` 預設)

**Request：**

```bash
curl -X GET "https://api.smartlock-saas.com/api/v1/knowledge-base/cases?brand=Yale&verified=true&limit=10" \
  -H "Authorization: Bearer {token}"
```

**Success Response（200 OK）：**

```json
{
  "data": [
    {
      "id": "case_01HQXM3A4B5C6D7E8F",
      "title": "Yale YDM4109 電池耗盡無法開鎖",
      "brand": "Yale",
      "model": "YDM4109",
      "tags": ["battery", "lockout", "keypad"],
      "verified": true,
      "created_at": "2026-02-17T09:00:00Z"
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_more": false,
    "total_count": 1
  }
}
```

---

#### `GET /api/v1/knowledge-base/cases/{id}`

取得單一案例詳情。

- **授權：** `admin`, `reviewer`

**Success Response（200 OK）：**

```json
{
  "id": "case_01HQXM3A4B5C6D7E8F",
  "title": "Yale YDM4109 電池耗盡無法開鎖",
  "problem_description": "用戶反映 Yale YDM4109 鍵盤完全無反應，無法輸入密碼開鎖。",
  "solution": "1. 使用 9V 電池緊急供電...",
  "brand": "Yale",
  "model": "YDM4109",
  "tags": ["battery", "lockout", "keypad"],
  "verified": true,
  "created_at": "2026-02-17T09:00:00Z",
  "updated_at": "2026-02-17T09:30:00Z"
}
```

---

#### `PUT /api/v1/knowledge-base/cases/{id}`

完整更新案例。更新內容會觸發 embedding 重新計算。

- **授權：** `admin`

**Request Body：**

```json
{
  "title": "Yale YDM4109 電池耗盡無法開鎖（更新版）",
  "problem_description": "用戶反映 Yale YDM4109 鍵盤完全無反應，電池指示燈閃爍紅燈。",
  "solution": "1. 使用 9V 電池緊急供電\n2. 輸入密碼開鎖\n3. 更換 4 顆 AA 鹼性電池（勿用充電電池）\n4. 重新測試\n5. 若仍無反應，檢查電池觸點是否氧化",
  "brand": "Yale",
  "model": "YDM4109",
  "tags": ["battery", "lockout", "keypad", "indicator"],
  "verified": true
}
```

**Success Response（200 OK）：** 回傳完整更新後的案例物件。

---

#### `DELETE /api/v1/knowledge-base/cases/{id}`

刪除案例。同時移除對應的 embedding 向量。

- **授權：** `admin`

**Success Response（204 No Content）：** 無回應 body。

**Error Responses：**

| 狀態碼 | error.code | 情境 |
|:---|:---|:---|
| `404` | `resource_not_found` | 案例不存在 |

---

#### `POST /api/v1/knowledge-base/cases/search`

向量語意搜尋。根據文字描述搜尋最相似的案例。

- **授權：** `admin`, `reviewer`

**Request Body：**

```json
{
  "query": "電子鎖鍵盤沒有反應，按了都沒有燈",
  "brand": "Yale",
  "limit": 5,
  "similarity_threshold": 0.75
}
```

**Success Response（200 OK）：**

```json
{
  "results": [
    {
      "id": "case_01HQXM3A4B5C6D7E8F",
      "title": "Yale YDM4109 電池耗盡無法開鎖",
      "problem_description": "用戶反映 Yale YDM4109 鍵盤完全無反應...",
      "solution": "1. 使用 9V 電池緊急供電...",
      "similarity_score": 0.92,
      "brand": "Yale",
      "model": "YDM4109"
    },
    {
      "id": "case_01HQXM4B5C6D7E8F9G",
      "title": "Samsung SHP-DP609 觸控面板失靈",
      "problem_description": "觸控面板無反應...",
      "solution": "1. 清潔面板表面...",
      "similarity_score": 0.78,
      "brand": "Samsung",
      "model": "SHP-DP609"
    }
  ],
  "query_embedding_tokens": 12
}
```

---

### 7.5 Knowledge Base - Manuals

#### `POST /api/v1/knowledge-base/manuals/upload`

上傳產品手冊 PDF，系統自動切割為 chunks 並建立 embeddings。

- **授權：** `admin`
- **Content-Type：** `multipart/form-data`
- **檔案限制：** 最大 50MB，僅支援 PDF

**Request：**

```bash
curl -X POST "https://api.smartlock-saas.com/api/v1/knowledge-base/manuals/upload" \
  -H "Authorization: Bearer {token}" \
  -F "file=@Yale_YDM4109_Manual.pdf" \
  -F "brand=Yale" \
  -F "model=YDM4109" \
  -F "title=Yale YDM4109 安裝與操作手冊"
```

**Success Response（202 Accepted）：**

```json
{
  "id": "manual_01HQXN5C6D7E8F9G0H",
  "title": "Yale YDM4109 安裝與操作手冊",
  "brand": "Yale",
  "model": "YDM4109",
  "file_name": "Yale_YDM4109_Manual.pdf",
  "file_size_bytes": 5242880,
  "status": "processing",
  "chunk_count": null,
  "created_at": "2026-02-17T10:00:00Z"
}
```

**Error Responses：**

| 狀態碼 | error.code | 情境 |
|:---|:---|:---|
| `400` | `file_too_large` | 檔案超過 50MB |
| `400` | `unsupported_file_type` | 非 PDF 檔案 |

---

#### `GET /api/v1/knowledge-base/manuals`

取得已上傳手冊列表。

- **授權：** `admin`, `reviewer`
- **分頁：** 支援
- **過濾參數：** `brand`, `model`, `status` (`processing`, `ready`, `failed`)

**Success Response（200 OK）：**

```json
{
  "data": [
    {
      "id": "manual_01HQXN5C6D7E8F9G0H",
      "title": "Yale YDM4109 安裝與操作手冊",
      "brand": "Yale",
      "model": "YDM4109",
      "file_name": "Yale_YDM4109_Manual.pdf",
      "file_size_bytes": 5242880,
      "status": "ready",
      "chunk_count": 142,
      "created_at": "2026-02-17T10:00:00Z"
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_more": false,
    "total_count": 1
  }
}
```

---

#### `DELETE /api/v1/knowledge-base/manuals/{id}`

刪除手冊及其所有 chunks 和 embeddings。

- **授權：** `admin`

**Success Response（204 No Content）：** 無回應 body。

---

### 7.6 SOP Drafts

#### `GET /api/v1/sop-drafts`

取得自動產生的 SOP 草稿列表。

- **授權：** `admin`, `reviewer`
- **分頁：** 支援
- **過濾參數：** `status` (`draft`, `approved`, `rejected`), `reviewer_id`
- **排序：** `sort_by` (`-created_at` 預設)

**Success Response（200 OK）：**

```json
{
  "data": [
    {
      "id": "sop_01HQXP6D7E8F9G0H1I",
      "case_event_id": "conv_01HQXK5V8N3M2P4R6T",
      "problem_card_id": "pc_01HQXK6A9B7C3D5E8F",
      "title": "Yale YDM4109 電池耗盡開鎖 SOP",
      "status": "draft",
      "reviewer_id": null,
      "created_at": "2026-02-17T09:45:00Z"
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_more": false,
    "total_count": 1
  }
}
```

---

#### `GET /api/v1/sop-drafts/{id}`

取得單一 SOP 草稿詳情（含步驟內容）。

- **授權：** `admin`, `reviewer`

**Success Response（200 OK）：**

```json
{
  "id": "sop_01HQXP6D7E8F9G0H1I",
  "case_event_id": "conv_01HQXK5V8N3M2P4R6T",
  "problem_card_id": "pc_01HQXK6A9B7C3D5E8F",
  "title": "Yale YDM4109 電池耗盡開鎖 SOP",
  "steps": [
    {
      "order": 1,
      "title": "確認症狀",
      "description": "確認鍵盤完全無反應，無背光、無聲音。"
    },
    {
      "order": 2,
      "title": "緊急供電",
      "description": "使用 9V 鹼性電池接觸鎖體底部的緊急供電觸點。"
    },
    {
      "order": 3,
      "title": "輸入密碼開鎖",
      "description": "在緊急供電狀態下，輸入管理員密碼開啟門鎖。"
    },
    {
      "order": 4,
      "title": "更換電池",
      "description": "拆開內面板，更換 4 顆 AA 鹼性電池，注意正負極方向。"
    },
    {
      "order": 5,
      "title": "功能測試",
      "description": "更換完成後測試密碼開鎖、指紋開鎖、卡片開鎖等所有功能。"
    }
  ],
  "status": "draft",
  "reviewer_id": null,
  "reviewed_at": null,
  "review_comment": null,
  "created_at": "2026-02-17T09:45:00Z"
}
```

---

#### `PATCH /api/v1/sop-drafts/{id}/review`

審核 SOP 草稿（核准或退回）。

- **授權：** `admin`, `reviewer`

**Request Body：**

```json
{
  "action": "approve",
  "comment": "步驟清晰完整，核准收錄。"
}
```

`action` 可選值：`approve`, `reject`

**Success Response（200 OK）：**

```json
{
  "id": "sop_01HQXP6D7E8F9G0H1I",
  "title": "Yale YDM4109 電池耗盡開鎖 SOP",
  "status": "approved",
  "reviewer_id": "user_01HQXA1B2C3D4E5F6G",
  "reviewed_at": "2026-02-17T11:00:00Z",
  "review_comment": "步驟清晰完整，核准收錄。",
  "created_at": "2026-02-17T09:45:00Z"
}
```

**Error Responses：**

| 狀態碼 | error.code | 情境 |
|:---|:---|:---|
| `400` | `parameter_invalid` | action 值不合法 |
| `409` | `resource_conflict` | SOP 已被審核過 |

---

#### `POST /api/v1/sop-drafts/{id}/adopt`

一鍵將已核准的 SOP 轉入案例庫（自動建立 CaseEntry）。

- **授權：** `admin`

**Request Body：** 無（或可選覆寫欄位）

```json
{
  "tags": ["battery", "lockout", "yale"]
}
```

**Success Response（201 Created）：**

```json
{
  "adopted_case_id": "case_01HQXQ7E8F9G0H1I2J",
  "sop_draft_id": "sop_01HQXP6D7E8F9G0H1I",
  "message": "SOP draft has been adopted as case entry successfully."
}
```

**Error Responses：**

| 狀態碼 | error.code | 情境 |
|:---|:---|:---|
| `409` | `resource_conflict` | SOP 狀態不是 approved |

---

### 7.7 Resolution Engine

#### `POST /api/v1/resolve`

觸發三層解決方案引擎（FAQ -> 知識庫 RAG -> LLM 生成）。此為內部 API，由 LINE Webhook 處理流程自動呼叫，也可手動觸發。

- **授權：** `admin`

**Request Body：**

```json
{
  "problem_card_id": "pc_01HQXK6A9B7C3D5E8F"
}
```

**Success Response（200 OK）：**

```json
{
  "problem_card_id": "pc_01HQXK6A9B7C3D5E8F",
  "resolution": {
    "layer_used": "knowledge_base_rag",
    "answer": "根據案例庫，Yale YDM4109 鍵盤無反應通常為電池耗盡。請使用 9V 電池接觸鎖體底部緊急供電觸點，同時輸入密碼開鎖後更換電池。",
    "confidence": 0.92,
    "source_case_ids": ["case_01HQXM3A4B5C6D7E8F"],
    "tokens_used": {
      "prompt_tokens": 850,
      "completion_tokens": 120,
      "total_tokens": 970
    }
  },
  "sop_draft_generated": true,
  "sop_draft_id": "sop_01HQXP6D7E8F9G0H1I"
}
```

**Resolution Layer 說明：**

| layer_used | 說明 |
|:---|:---|
| `faq_match` | FAQ 精確匹配 |
| `knowledge_base_rag` | 知識庫 RAG 語意搜尋 |
| `llm_generation` | LLM 直接生成（無足夠案例） |
| `escalation` | 三層均無法解決，轉人工 |

**Error Responses：**

| 狀態碼 | error.code | 情境 |
|:---|:---|:---|
| `404` | `resource_not_found` | 問題卡不存在 |
| `500` | `resolution_failed` | 引擎執行異常 |

---

### 7.8 Auth

#### `POST /api/v1/auth/login`

管理員登入，取得 JWT Token。

- **授權：** 公開（無需 Token）

**Request Body：**

```json
{
  "username": "admin@example.com",
  "password": "secure_password_123"
}
```

**Success Response（200 OK）：**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4...",
  "user": {
    "id": "user_01HQXA1B2C3D4E5F6G",
    "username": "admin@example.com",
    "role": "admin"
  }
}
```

**Error Responses：**

| 狀態碼 | error.code | 情境 |
|:---|:---|:---|
| `401` | `authentication_failed` | 帳號或密碼錯誤 |
| `429` | `rate_limit_exceeded` | 登入嘗試次數過多 |

---

#### `POST /api/v1/auth/refresh`

以 Refresh Token 取得新的 Access Token。

- **授權：** 公開（無需 Bearer Token）

**Request Body：**

```json
{
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4..."
}
```

**Success Response（200 OK）：**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "bmV3IHJlZnJlc2ggdG9rZW4..."
}
```

**Error Responses：**

| 狀態碼 | error.code | 情境 |
|:---|:---|:---|
| `401` | `token_expired` | Refresh Token 已過期 |
| `401` | `authentication_failed` | Refresh Token 無效 |

---

#### `POST /api/v1/auth/logout`

登出，撤銷目前的 Token。

- **授權：** `admin`, `reviewer`

**Request Body：**

```json
{
  "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4..."
}
```

**Success Response（200 OK）：**

```json
{
  "message": "Successfully logged out."
}
```

---

### 7.9 Dashboard

#### `GET /api/v1/dashboard/stats`

取得儀表板統計數據。

- **授權：** `admin`
- **查詢參數：** `period` (`today`, `7d`, `30d`, `90d`，預設 `7d`)

**Request：**

```bash
curl -X GET "https://api.smartlock-saas.com/api/v1/dashboard/stats?period=30d" \
  -H "Authorization: Bearer {token}"
```

**Success Response（200 OK）：**

```json
{
  "period": "30d",
  "conversations": {
    "total": 1250,
    "active": 32,
    "resolved": 1180,
    "escalated": 38
  },
  "resolution": {
    "ai_resolution_rate": 0.856,
    "avg_resolution_time_seconds": 125,
    "by_layer": {
      "faq_match": 320,
      "knowledge_base_rag": 750,
      "llm_generation": 142,
      "escalation": 38
    }
  },
  "hot_topics": [
    {"topic": "電池耗盡", "count": 215},
    {"topic": "密碼重設", "count": 180},
    {"topic": "藍牙連線失敗", "count": 95},
    {"topic": "安裝問題", "count": 72},
    {"topic": "指紋辨識失敗", "count": 68}
  ],
  "token_usage": {
    "total_tokens": 2450000,
    "prompt_tokens": 1850000,
    "completion_tokens": 600000,
    "estimated_cost_usd": 12.50
  },
  "top_brands": [
    {"brand": "Yale", "count": 420},
    {"brand": "Samsung", "count": 380},
    {"brand": "Gateman", "count": 250}
  ]
}
```

---

### 7.10 System Config

#### `GET /api/v1/config`

取得系統設定。

- **授權：** `admin`

**Success Response（200 OK）：**

```json
{
  "rag": {
    "similarity_threshold": 0.75,
    "max_results": 5,
    "chunk_size": 512,
    "chunk_overlap": 50
  },
  "llm": {
    "model": "gpt-4o",
    "temperature": 0.3,
    "max_tokens": 1024,
    "system_prompt_version": "v2.1"
  },
  "resolution": {
    "faq_confidence_threshold": 0.95,
    "rag_confidence_threshold": 0.75,
    "auto_escalation_enabled": true
  },
  "line_bot": {
    "greeting_message_enabled": true,
    "max_conversation_turns": 20
  }
}
```

---

#### `PATCH /api/v1/config`

更新系統設定（部分更新）。

- **授權：** `admin`

**Request Body：**

```json
{
  "rag": {
    "similarity_threshold": 0.80
  },
  "llm": {
    "temperature": 0.2
  }
}
```

**Success Response（200 OK）：** 回傳完整的更新後設定物件（同 GET /config 格式）。

**Error Responses：**

| 狀態碼 | error.code | 情境 |
|:---|:---|:---|
| `400` | `parameter_invalid` | 設定值超出允許範圍 |

---

## 8. V2.0 API 端點詳述

### 8.1 Technicians

#### `POST /api/v1/technicians/register`

技師註冊。

- **授權：** 公開（無需 Token），或由 `admin` 代為建立

**Request Body：**

```json
{
  "name": "王大明",
  "phone": "0912345678",
  "email": "daming.wang@example.com",
  "password": "secure_password",
  "capabilities": ["yale", "samsung", "gateman", "battery_replacement", "lock_installation"],
  "regions": ["taipei_daan", "taipei_xinyi", "taipei_songshan"],
  "id_number_hash": "a1b2c3d4e5f6..."
}
```

**Success Response（201 Created）：**

```json
{
  "id": "tech_01HQXR8F9G0H1I2J3K",
  "name": "王大明",
  "phone": "0912345678",
  "email": "daming.wang@example.com",
  "capabilities": ["yale", "samsung", "gateman", "battery_replacement", "lock_installation"],
  "regions": ["taipei_daan", "taipei_xinyi", "taipei_songshan"],
  "rating": null,
  "status": "pending_approval",
  "created_at": "2026-02-17T10:00:00Z"
}
```

---

#### `POST /api/v1/technicians/login`

技師登入，取得 JWT Token。

- **授權：** 公開

**Request Body：**

```json
{
  "phone": "0912345678",
  "password": "secure_password"
}
```

**Success Response（200 OK）：**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "dGVjaG5pY2lhbiByZWZyZXNo...",
  "technician": {
    "id": "tech_01HQXR8F9G0H1I2J3K",
    "name": "王大明",
    "role": "technician",
    "status": "active"
  }
}
```

---

#### `GET /api/v1/technicians/me`

取得目前登入技師的個人資料。

- **授權：** `technician`

**Success Response（200 OK）：**

```json
{
  "id": "tech_01HQXR8F9G0H1I2J3K",
  "name": "王大明",
  "phone": "0912345678",
  "email": "daming.wang@example.com",
  "capabilities": ["yale", "samsung", "gateman", "battery_replacement", "lock_installation"],
  "regions": ["taipei_daan", "taipei_xinyi", "taipei_songshan"],
  "rating": 4.8,
  "total_completed_orders": 156,
  "status": "active",
  "created_at": "2026-02-17T10:00:00Z"
}
```

---

#### `PATCH /api/v1/technicians/me`

技師更新自己的資料（能力、服務區域、聯絡方式）。

- **授權：** `technician`

**Request Body：**

```json
{
  "capabilities": ["yale", "samsung", "gateman", "battery_replacement", "lock_installation", "deadbolt_repair"],
  "regions": ["taipei_daan", "taipei_xinyi", "taipei_songshan", "taipei_zhongshan"]
}
```

**Success Response（200 OK）：** 回傳完整更新後的技師資料物件。

---

### 8.2 Work Orders

#### `GET /api/v1/work-orders`

取得工單列表。技師僅可看到符合自身能力與區域的可接單工單及自身工單；管理員可看到全部。

- **授權：** `admin`, `technician`
- **分頁：** 支援
- **過濾參數：** `status` (`pending`, `assigned`, `accepted`, `in_progress`, `completed`, `confirmed`, `cancelled`), `technician_id`, `brand`, `created_after`, `created_before`
- **排序：** `sort_by` (`-created_at` 預設)

**Success Response（200 OK）：**

```json
{
  "data": [
    {
      "id": "wo_01HQXS9G0H1I2J3K4L",
      "problem_card_id": "pc_01HQXK6A9B7C3D5E8F",
      "technician_id": null,
      "status": "pending",
      "brand": "Yale",
      "model": "YDM4109",
      "location": "台北市大安區忠孝東路四段100號12樓",
      "symptoms_summary": "鍵盤無反應，疑似電池耗盡",
      "price": null,
      "created_at": "2026-02-17T10:30:00Z"
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_more": false,
    "total_count": 1
  }
}
```

---

#### `GET /api/v1/work-orders/{id}`

取得單一工單詳情。

- **授權：** `admin`, `technician`（僅限自身工單或可接單的工單）

**Success Response（200 OK）：**

```json
{
  "id": "wo_01HQXS9G0H1I2J3K4L",
  "problem_card_id": "pc_01HQXK6A9B7C3D5E8F",
  "problem_card": {
    "brand": "Yale",
    "model": "YDM4109",
    "location": "台北市大安區忠孝東路四段100號12樓",
    "door_status": "locked_out",
    "symptoms": ["no_response", "battery_low_indicator"]
  },
  "technician_id": "tech_01HQXR8F9G0H1I2J3K",
  "technician_name": "王大明",
  "status": "accepted",
  "price": {
    "base_price": 800,
    "surcharges": [
      {"name": "night_service", "amount": 300}
    ],
    "total": 1100
  },
  "scheduled_at": "2026-02-17T14:00:00Z",
  "completion_report": null,
  "created_at": "2026-02-17T10:30:00Z",
  "updated_at": "2026-02-17T11:00:00Z"
}
```

---

#### `POST /api/v1/work-orders/{id}/accept`

技師接受工單。

- **授權：** `technician`

**Request Body：**

```json
{
  "estimated_arrival_minutes": 45,
  "scheduled_at": "2026-02-17T14:00:00Z"
}
```

**Success Response（200 OK）：**

```json
{
  "id": "wo_01HQXS9G0H1I2J3K4L",
  "status": "accepted",
  "technician_id": "tech_01HQXR8F9G0H1I2J3K",
  "scheduled_at": "2026-02-17T14:00:00Z",
  "estimated_arrival_minutes": 45,
  "updated_at": "2026-02-17T11:00:00Z"
}
```

**Error Responses：**

| 狀態碼 | error.code | 情境 |
|:---|:---|:---|
| `409` | `work_order_state_invalid` | 工單已被其他技師接走 |

---

#### `POST /api/v1/work-orders/{id}/complete`

技師回報工單完成（含照片、材料清單）。

- **授權：** `technician`
- **Content-Type：** `multipart/form-data`

**Request：**

```bash
curl -X POST "https://api.smartlock-saas.com/api/v1/work-orders/wo_01HQXS9G0H1I2J3K4L/complete" \
  -H "Authorization: Bearer {token}" \
  -F "summary=已更換電池，鍵盤功能恢復正常" \
  -F "materials_used=[{\"name\":\"AA鹼性電池\",\"quantity\":4,\"unit_price\":15}]" \
  -F "photos[]=@before.jpg" \
  -F "photos[]=@after.jpg"
```

**Success Response（200 OK）：**

```json
{
  "id": "wo_01HQXS9G0H1I2J3K4L",
  "status": "completed",
  "completion_report": {
    "summary": "已更換電池，鍵盤功能恢復正常",
    "materials_used": [
      {"name": "AA鹼性電池", "quantity": 4, "unit_price": 15}
    ],
    "photo_urls": [
      "https://storage.smartlock-saas.com/wo/wo_01HQXS9G0H1I2J3K4L/before.jpg",
      "https://storage.smartlock-saas.com/wo/wo_01HQXS9G0H1I2J3K4L/after.jpg"
    ],
    "completed_at": "2026-02-17T15:30:00Z"
  },
  "updated_at": "2026-02-17T15:30:00Z"
}
```

**Error Responses：**

| 狀態碼 | error.code | 情境 |
|:---|:---|:---|
| `409` | `work_order_state_invalid` | 工單狀態不是 accepted 或 in_progress |

---

#### `POST /api/v1/work-orders/{id}/confirm`

客戶或管理員確認工單完成。

- **授權：** `admin`

**Request Body：**

```json
{
  "rating": 5,
  "feedback": "師傅很專業，快速解決問題。"
}
```

**Success Response（200 OK）：**

```json
{
  "id": "wo_01HQXS9G0H1I2J3K4L",
  "status": "confirmed",
  "rating": 5,
  "feedback": "師傅很專業，快速解決問題。",
  "confirmed_at": "2026-02-17T16:00:00Z",
  "updated_at": "2026-02-17T16:00:00Z"
}
```

---

### 8.3 Dispatch Engine

#### `POST /api/v1/dispatch/auto-match`

根據問題卡自動媒合最佳技師。考量因素：能力匹配、服務區域、評分、當前工作量。

- **授權：** `admin`

**Request Body：**

```json
{
  "problem_card_id": "pc_01HQXK6A9B7C3D5E8F",
  "urgency": "normal",
  "max_candidates": 3
}
```

`urgency` 可選值：`low`, `normal`, `urgent`, `emergency`

**Success Response（200 OK）：**

```json
{
  "problem_card_id": "pc_01HQXK6A9B7C3D5E8F",
  "candidates": [
    {
      "technician_id": "tech_01HQXR8F9G0H1I2J3K",
      "name": "王大明",
      "match_score": 0.95,
      "distance_km": 2.3,
      "estimated_arrival_minutes": 25,
      "current_workload": 1,
      "rating": 4.8
    },
    {
      "technician_id": "tech_01HQXT0H1I2J3K4L5M",
      "name": "李小華",
      "match_score": 0.88,
      "distance_km": 5.1,
      "estimated_arrival_minutes": 40,
      "current_workload": 0,
      "rating": 4.6
    }
  ],
  "work_order_id": null
}
```

**Error Responses：**

| 狀態碼 | error.code | 情境 |
|:---|:---|:---|
| `422` | `dispatch_no_match` | 沒有符合條件的技師 |

---

#### `POST /api/v1/dispatch/assign`

手動指派技師（管理員操作）。會自動建立工單。

- **授權：** `admin`

**Request Body：**

```json
{
  "problem_card_id": "pc_01HQXK6A9B7C3D5E8F",
  "technician_id": "tech_01HQXR8F9G0H1I2J3K",
  "note": "客戶指定王師傅"
}
```

**Success Response（201 Created）：**

```json
{
  "work_order_id": "wo_01HQXS9G0H1I2J3K4L",
  "problem_card_id": "pc_01HQXK6A9B7C3D5E8F",
  "technician_id": "tech_01HQXR8F9G0H1I2J3K",
  "status": "assigned",
  "note": "客戶指定王師傅",
  "created_at": "2026-02-17T11:30:00Z"
}
```

---

### 8.4 Pricing

#### `POST /api/v1/pricing/calculate`

根據問題卡資訊計算預估價格。

- **授權：** `admin`, `technician`

**Request Body：**

```json
{
  "brand": "Yale",
  "model": "YDM4109",
  "lock_type": "digital_deadbolt",
  "difficulty": "simple",
  "is_emergency": false,
  "is_night_service": true,
  "additional_items": ["battery_replacement"]
}
```

**Success Response（200 OK）：**

```json
{
  "base_price": 800,
  "surcharges": [
    {"name": "night_service", "amount": 300, "reason": "夜間服務（18:00-08:00）"},
    {"name": "battery_replacement", "amount": 60, "reason": "電池更換（4 顆 AA）"}
  ],
  "discount": 0,
  "total": 1160,
  "currency": "TWD",
  "price_rule_ids": ["rule_01HQXU1I2J3K4L5M6N"],
  "note": "此為預估價格，實際費用以現場評估為準。"
}
```

---

#### `GET /api/v1/pricing/rules`

取得計價規則列表。

- **授權：** `admin`
- **分頁：** 支援
- **過濾參數：** `brand`, `lock_type`, `difficulty`

**Success Response（200 OK）：**

```json
{
  "data": [
    {
      "id": "rule_01HQXU1I2J3K4L5M6N",
      "brand": "Yale",
      "lock_type": "digital_deadbolt",
      "difficulty": "simple",
      "base_price": 800,
      "surcharges": [
        {"name": "night_service", "condition": "18:00-08:00", "amount": 300},
        {"name": "emergency", "condition": "urgency=emergency", "amount": 500},
        {"name": "holiday", "condition": "national_holiday", "amount": 400}
      ],
      "created_at": "2026-01-15T10:00:00Z",
      "updated_at": "2026-02-01T14:00:00Z"
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_more": false,
    "total_count": 1
  }
}
```

---

#### `POST /api/v1/pricing/rules`

建立新計價規則。

- **授權：** `admin`

**Request Body：**

```json
{
  "brand": "Samsung",
  "lock_type": "digital_deadbolt",
  "difficulty": "moderate",
  "base_price": 1200,
  "surcharges": [
    {"name": "night_service", "condition": "18:00-08:00", "amount": 400},
    {"name": "emergency", "condition": "urgency=emergency", "amount": 600}
  ]
}
```

**Success Response（201 Created）：** 回傳完整的規則物件。

---

#### `PUT /api/v1/pricing/rules/{id}`

更新計價規則。

- **授權：** `admin`

**Request Body：** 同 POST，完整替換。

**Success Response（200 OK）：** 回傳完整更新後的規則物件。

**Error Responses：**

| 狀態碼 | error.code | 情境 |
|:---|:---|:---|
| `404` | `resource_not_found` | 規則不存在 |

---

### 8.5 Accounting

#### `GET /api/v1/accounting/reconciliations`

取得對帳記錄列表。

- **授權：** `admin`
- **分頁：** 支援
- **過濾參數：** `status` (`pending`, `approved`, `disputed`), `technician_id`, `period_start`, `period_end`

**Success Response（200 OK）：**

```json
{
  "data": [
    {
      "id": "recon_01HQXV2J3K4L5M6N7O",
      "technician_id": "tech_01HQXR8F9G0H1I2J3K",
      "technician_name": "王大明",
      "period_start": "2026-02-01T00:00:00Z",
      "period_end": "2026-02-15T23:59:59Z",
      "total_orders": 12,
      "total_revenue": 15600,
      "platform_fee": 2340,
      "technician_payout": 13260,
      "status": "pending",
      "created_at": "2026-02-16T00:00:00Z"
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_more": false,
    "total_count": 1
  }
}
```

---

#### `POST /api/v1/accounting/reconciliations/{id}/approve`

核准對帳記錄，觸發結算流程。

- **授權：** `admin`

**Request Body：**

```json
{
  "note": "已核對完畢，金額正確。"
}
```

**Success Response（200 OK）：**

```json
{
  "id": "recon_01HQXV2J3K4L5M6N7O",
  "status": "approved",
  "approved_by": "user_01HQXA1B2C3D4E5F6G",
  "approved_at": "2026-02-17T12:00:00Z",
  "settlement_id": "settle_01HQXW3K4L5M6N7O8P"
}
```

---

#### `GET /api/v1/accounting/settlements`

取得結算記錄列表。

- **授權：** `admin`
- **分頁：** 支援
- **過濾參數：** `status` (`pending`, `paid`, `failed`), `technician_id`

**Success Response（200 OK）：**

```json
{
  "data": [
    {
      "id": "settle_01HQXW3K4L5M6N7O8P",
      "reconciliation_id": "recon_01HQXV2J3K4L5M6N7O",
      "technician_id": "tech_01HQXR8F9G0H1I2J3K",
      "technician_name": "王大明",
      "amount": 13260,
      "currency": "TWD",
      "status": "pending",
      "payment_method": "bank_transfer",
      "created_at": "2026-02-17T12:00:00Z"
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_more": false,
    "total_count": 1
  }
}
```

---

#### `GET /api/v1/accounting/vouchers`

取得憑證列表。

- **授權：** `admin`
- **分頁：** 支援
- **過濾參數：** `work_order_id`, `technician_id`, `created_after`, `created_before`

**Success Response（200 OK）：**

```json
{
  "data": [
    {
      "id": "voucher_01HQXX4L5M6N7O8P9Q",
      "work_order_id": "wo_01HQXS9G0H1I2J3K4L",
      "type": "service_receipt",
      "amount": 1160,
      "currency": "TWD",
      "issued_at": "2026-02-17T16:00:00Z"
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_more": false,
    "total_count": 1
  }
}
```

---

#### `GET /api/v1/accounting/vouchers/{id}/export`

匯出單一憑證為 PDF。

- **授權：** `admin`
- **回應：** `application/pdf` binary stream

**Request：**

```bash
curl -X GET "https://api.smartlock-saas.com/api/v1/accounting/vouchers/voucher_01HQXX4L5M6N7O8P9Q/export" \
  -H "Authorization: Bearer {token}" \
  -o voucher.pdf
```

**Success Response（200 OK）：** 回傳 PDF 檔案。

| Header | 值 |
|:---|:---|
| `Content-Type` | `application/pdf` |
| `Content-Disposition` | `attachment; filename="voucher_01HQXX4L5M6N7O8P9Q.pdf"` |

---

### 8.6 Notifications

#### `POST /api/v1/notifications/push`

推播通知給技師（新工單、工單更新等）。

- **授權：** `admin`（系統內部使用，也可由管理員手動觸發）

**Request Body：**

```json
{
  "target_type": "technician",
  "target_id": "tech_01HQXR8F9G0H1I2J3K",
  "notification_type": "new_work_order",
  "title": "新工單通知",
  "body": "台北市大安區有一筆 Yale 電子鎖維修工單，請查看。",
  "data": {
    "work_order_id": "wo_01HQXS9G0H1I2J3K4L"
  },
  "channels": ["push", "sms"]
}
```

`notification_type` 可選值：`new_work_order`, `order_assigned`, `order_cancelled`, `payment_received`, `system_announcement`

`channels` 可選值：`push`, `sms`, `line`

**Success Response（202 Accepted）：**

```json
{
  "notification_id": "notif_01HQXY5M6N7O8P9Q0R",
  "status": "queued",
  "channels_targeted": ["push", "sms"],
  "created_at": "2026-02-17T11:30:00Z"
}
```

**Error Responses：**

| 狀態碼 | error.code | 情境 |
|:---|:---|:---|
| `404` | `resource_not_found` | 目標技師不存在 |
| `400` | `parameter_invalid` | 無效的通知類型或通道 |

---

## 9. 資料模型/Schema 定義

### 9.1 `Conversation`

對話記錄，對應一個 LINE 用戶的一次問題諮詢流程。

```json
{
  "id": "string (conv_...)",
  "line_user_id": "string (LINE User ID)",
  "status": "string (active | resolved | escalated)",
  "problem_card_id": "string | null (pc_...)",
  "messages": [
    {
      "id": "string (msg_...)",
      "role": "string (user | assistant | system)",
      "type": "string (text | image)",
      "content": "string",
      "timestamp": "string (ISO 8601)"
    }
  ],
  "message_count": "integer",
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)"
}
```

### 9.2 `ProblemCard`

結構化診斷問題卡，由 AI 自動從對話中提取。

```json
{
  "id": "string (pc_...)",
  "conversation_id": "string (conv_...)",
  "brand": "string",
  "model": "string",
  "location": "string",
  "door_status": "string (locked_out | partially_functional | normal)",
  "network_status": "string (online | offline | unknown)",
  "symptoms": ["string"],
  "intent": "string (unlock_request | repair_request | installation | inquiry)",
  "status": "string (open | in_progress | resolved | escalated)",
  "created_at": "string (ISO 8601)"
}
```

### 9.3 `CaseEntry`

知識庫案例，用於 RAG 檢索。

```json
{
  "id": "string (case_...)",
  "title": "string",
  "problem_description": "string",
  "solution": "string",
  "brand": "string",
  "model": "string",
  "tags": ["string"],
  "verified": "boolean",
  "embedding_status": "string (processing | ready | failed)",
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)"
}
```

### 9.4 `Manual`

產品手冊，上傳後自動切割為 chunks。

```json
{
  "id": "string (manual_...)",
  "title": "string",
  "brand": "string",
  "model": "string",
  "file_name": "string",
  "file_size_bytes": "integer",
  "status": "string (processing | ready | failed)",
  "chunk_count": "integer | null",
  "created_at": "string (ISO 8601)"
}
```

### 9.5 `SOPDraft`

AI 自動產生的 SOP 草稿。

```json
{
  "id": "string (sop_...)",
  "case_event_id": "string (conv_...)",
  "problem_card_id": "string (pc_...)",
  "title": "string",
  "steps": [
    {
      "order": "integer",
      "title": "string",
      "description": "string"
    }
  ],
  "status": "string (draft | approved | rejected)",
  "reviewer_id": "string | null (user_...)",
  "reviewed_at": "string | null (ISO 8601)",
  "review_comment": "string | null",
  "created_at": "string (ISO 8601)"
}
```

### 9.6 `WorkOrder` (V2.0)

派工工單，連結問題卡與技師。

```json
{
  "id": "string (wo_...)",
  "problem_card_id": "string (pc_...)",
  "problem_card": "ProblemCard (expanded)",
  "technician_id": "string | null (tech_...)",
  "technician_name": "string | null",
  "status": "string (pending | assigned | accepted | in_progress | completed | confirmed | cancelled)",
  "price": {
    "base_price": "number",
    "surcharges": [
      {
        "name": "string",
        "amount": "number"
      }
    ],
    "total": "number"
  },
  "scheduled_at": "string | null (ISO 8601)",
  "estimated_arrival_minutes": "integer | null",
  "completion_report": {
    "summary": "string",
    "materials_used": [
      {
        "name": "string",
        "quantity": "integer",
        "unit_price": "number"
      }
    ],
    "photo_urls": ["string"],
    "completed_at": "string (ISO 8601)"
  },
  "rating": "integer | null (1-5)",
  "feedback": "string | null",
  "confirmed_at": "string | null (ISO 8601)",
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)"
}
```

**工單狀態流轉：**

```
pending -> assigned -> accepted -> in_progress -> completed -> confirmed
   |          |           |             |              |
   +--------- +--------- +------------ +------------- +----> cancelled
```

### 9.7 `Technician` (V2.0)

技師資料。

```json
{
  "id": "string (tech_...)",
  "name": "string",
  "phone": "string",
  "email": "string",
  "capabilities": ["string"],
  "regions": ["string"],
  "rating": "number | null (1.0 - 5.0)",
  "total_completed_orders": "integer",
  "status": "string (pending_approval | active | inactive | suspended)",
  "created_at": "string (ISO 8601)"
}
```

### 9.8 `PriceRule` (V2.0)

計價規則定義。

```json
{
  "id": "string (rule_...)",
  "brand": "string",
  "lock_type": "string (digital_deadbolt | smart_lock | padlock | other)",
  "difficulty": "string (simple | moderate | complex)",
  "base_price": "number (TWD)",
  "surcharges": [
    {
      "name": "string",
      "condition": "string",
      "amount": "number (TWD)"
    }
  ],
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)"
}
```

### 9.9 `Reconciliation` (V2.0)

對帳記錄。

```json
{
  "id": "string (recon_...)",
  "technician_id": "string (tech_...)",
  "technician_name": "string",
  "period_start": "string (ISO 8601)",
  "period_end": "string (ISO 8601)",
  "total_orders": "integer",
  "total_revenue": "number (TWD)",
  "platform_fee": "number (TWD)",
  "technician_payout": "number (TWD)",
  "status": "string (pending | approved | disputed)",
  "approved_by": "string | null (user_...)",
  "approved_at": "string | null (ISO 8601)",
  "created_at": "string (ISO 8601)"
}
```

### 9.10 `Settlement` (V2.0)

結算記錄。

```json
{
  "id": "string (settle_...)",
  "reconciliation_id": "string (recon_...)",
  "technician_id": "string (tech_...)",
  "technician_name": "string",
  "amount": "number (TWD)",
  "currency": "string (TWD)",
  "status": "string (pending | paid | failed)",
  "payment_method": "string (bank_transfer | other)",
  "paid_at": "string | null (ISO 8601)",
  "created_at": "string (ISO 8601)"
}
```

### 9.11 `Notification` (V2.0)

通知記錄。

```json
{
  "id": "string (notif_...)",
  "target_type": "string (technician)",
  "target_id": "string (tech_...)",
  "notification_type": "string (new_work_order | order_assigned | order_cancelled | payment_received | system_announcement)",
  "title": "string",
  "body": "string",
  "data": "object | null",
  "channels": ["string (push | sms | line)"],
  "status": "string (queued | sent | delivered | failed)",
  "created_at": "string (ISO 8601)"
}
```

---

## 10. API 生命週期與版本控制

### 10.1 版本策略

使用 URL path versioning：`/api/v1/...`

**向後相容變更（不改版本號）：**
- 新增 API 端點
- 回應中新增欄位
- 新增可選的請求參數

**破壞性變更（需升版 v1 -> v2）：**
- 刪除或重命名欄位/端點
- 修改現有欄位型別
- 新增必填參數

### 10.2 棄用策略

1. 至少提前 **3 個月** 通知棄用。
2. 在回應 Header 中加入 `Deprecation: true` 及 `Sunset: <date>`。
3. 於 API 文件和 Dashboard 公告中標註。
4. 提供遷移指南文件。
5. 棄用期間仍維持功能正常。
6. Sunset date 後回傳 `410 Gone`。

---

## 11. 附錄

### 11.1 完整 cURL 範例

#### 登入並取得 Token

```bash
# Login
TOKEN=$(curl -s -X POST "https://api.smartlock-saas.com/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin@example.com", "password": "your_password"}' \
  | jq -r '.access_token')

echo "Token: $TOKEN"
```

#### 查看對話列表

```bash
curl -s -X GET "https://api.smartlock-saas.com/api/v1/conversations?status=active&limit=5" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" | jq .
```

#### 建立問題卡

```bash
curl -s -X POST "https://api.smartlock-saas.com/api/v1/problem-cards" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv_01HQXK5V8N3M2P4R6T",
    "brand": "Yale",
    "model": "YDM4109",
    "location": "台北市大安區忠孝東路四段100號12樓",
    "door_status": "locked_out",
    "network_status": "offline",
    "symptoms": ["no_response", "battery_low_indicator"],
    "intent": "unlock_request"
  }' | jq .
```

#### 知識庫語意搜尋

```bash
curl -s -X POST "https://api.smartlock-saas.com/api/v1/knowledge-base/cases/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "電子鎖鍵盤沒有反應",
    "brand": "Yale",
    "limit": 3,
    "similarity_threshold": 0.75
  }' | jq .
```

#### 觸發解決方案引擎

```bash
curl -s -X POST "https://api.smartlock-saas.com/api/v1/resolve" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"problem_card_id": "pc_01HQXK6A9B7C3D5E8F"}' | jq .
```

#### 上傳產品手冊

```bash
curl -s -X POST "https://api.smartlock-saas.com/api/v1/knowledge-base/manuals/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@Yale_YDM4109_Manual.pdf" \
  -F "brand=Yale" \
  -F "model=YDM4109" \
  -F "title=Yale YDM4109 安裝與操作手冊" | jq .
```

#### V2.0：自動媒合技師

```bash
curl -s -X POST "https://api.smartlock-saas.com/api/v1/dispatch/auto-match" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "problem_card_id": "pc_01HQXK6A9B7C3D5E8F",
    "urgency": "normal",
    "max_candidates": 3
  }' | jq .
```

#### V2.0：計算報價

```bash
curl -s -X POST "https://api.smartlock-saas.com/api/v1/pricing/calculate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "brand": "Yale",
    "model": "YDM4109",
    "lock_type": "digital_deadbolt",
    "difficulty": "simple",
    "is_emergency": false,
    "is_night_service": true,
    "additional_items": ["battery_replacement"]
  }' | jq .
```

---

**文件審核記錄：**

| 日期 | 審核人 | 版本 | 變更摘要 |
|:---|:---|:---|:---|
| 2026-02-17 | 開發團隊 | v1.0 | 初版：V1.0 + V2.0 完整 API 規範 |
