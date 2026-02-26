# 部署與運維指南 - 電子鎖智能客服與派工平台

# Deployment and Operations Guide - Smart Lock AI Support & Service Dispatch SaaS Platform

---

**文件版本 (Document Version):** `v1.0`
**最後更新 (Last Updated):** `2026-02-25`
**主要作者 (Lead Author):** `DevOps / 技術負責人`
**審核者 (Reviewers):** `架構委員會, 核心開發團隊`
**狀態 (Status):** `草稿 (Draft)`

---

## 目錄 (Table of Contents)

- [第 1 部分：部署架構總覽](#第-1-部分部署架構總覽)
  - [1.1 環境策略](#11-環境策略)
  - [1.2 部署拓撲圖 (Docker Compose)](#12-部署拓撲圖-docker-compose)
  - [1.3 容器服務清單](#13-容器服務清單)
  - [1.4 網路與端口規劃](#14-網路與端口規劃)
- [第 2 部分：CI/CD 流水線](#第-2-部分cicd-流水線)
  - [2.1 流水線概覽](#21-流水線概覽)
  - [2.2 ci.yml - 持續整合](#22-ciyml---持續整合)
  - [2.3 deploy.yml - 持續部署](#23-deployyml---持續部署)
  - [2.4 CI/CD 步驟詳細說明](#24-cicd-步驟詳細說明)
- [第 3 部分：部署檢查清單](#第-3-部分部署檢查清單)
  - [3.1 部署前檢查](#31-部署前檢查)
  - [3.2 部署中監控](#32-部署中監控)
  - [3.3 部署後驗證](#33-部署後驗證)
- [第 4 部分：部署策略](#第-4-部分部署策略)
  - [4.1 Blue-Green 部署 (生產環境)](#41-blue-green-部署-生產環境)
  - [4.2 滾動部署 (Staging 環境)](#42-滾動部署-staging-環境)
  - [4.3 首次部署流程](#43-首次部署流程)
- [第 5 部分：監控與告警](#第-5-部分監控與告警)
  - [5.1 應用程式指標](#51-應用程式指標)
  - [5.2 基礎設施指標](#52-基礎設施指標)
  - [5.3 業務指標](#53-業務指標)
  - [5.4 告警配置](#54-告警配置)
  - [5.5 日誌管理](#55-日誌管理)
- [第 6 部分：回滾程序](#第-6-部分回滾程序)
  - [6.1 自動回滾觸發條件](#61-自動回滾觸發條件)
  - [6.2 手動回滾流程](#62-手動回滾流程)
  - [6.3 資料庫回滾](#63-資料庫回滾)
- [第 7 部分：基礎設施即程式碼](#第-7-部分基礎設施即程式碼)
  - [7.1 Docker Compose 配置](#71-docker-compose-配置)
  - [7.2 Nginx 反向代理配置](#72-nginx-反向代理配置)
  - [7.3 Dockerfile 配置](#73-dockerfile-配置)
- [第 8 部分：部署安全性](#第-8-部分部署安全性)
  - [8.1 密鑰管理](#81-密鑰管理)
  - [8.2 網路安全](#82-網路安全)
  - [8.3 容器安全](#83-容器安全)
  - [8.4 外部服務安全](#84-外部服務安全)
- [第 9 部分：運維手冊 (Runbook)](#第-9-部分運維手冊-runbook)
  - [9.1 資料庫遷移](#91-資料庫遷移)
  - [9.2 手動備份](#92-手動備份)
  - [9.3 服務重啟](#93-服務重啟)
  - [9.4 水平擴展](#94-水平擴展)
  - [9.5 日誌查詢](#95-日誌查詢)
  - [9.6 SSL 憑證更新](#96-ssl-憑證更新)
  - [9.7 密鑰輪替](#97-密鑰輪替)
  - [9.8 災難復原](#98-災難復原)
- [第 10 部分：環境專屬配置](#第-10-部分環境專屬配置)
  - [10.1 Development 環境](#101-development-環境)
  - [10.2 Staging 環境](#102-staging-環境)
  - [10.3 Production 環境](#103-production-環境)
  - [10.4 環境變數完整清單](#104-環境變數完整清單)

---

**目的**: 本文件為「電子鎖智能客服與派工 SaaS 平台」提供完整的部署流程、基礎設施管理與日常運維操作指南。涵蓋從開發環境到生產環境的部署架構、CI/CD 流水線、監控告警、回滾策略及常見運維操作手冊，確保系統可靠、穩定地運行於生產環境中。

**參考文件：**
- `docs/05_architecture_and_design_document.md` — 第 6 部分：部署與基礎設施、第 7 部分：跨領域考量
- `docs/08_project_structure_guide.md` — 第 6 節：Docker 與部署結構、第 7 節：設定檔結構
- `docs/06_api_design_specification.md` — API 端點與健康檢查規範

---

## 第 1 部分：部署架構總覽

### 1.1 環境策略

系統採用三環境策略，從開發到生產逐步推進：

```
Development (localhost)  →  Staging (VPS)  →  Production (VPS/Cloud)
        ↓                       ↓                    ↓
    功能開發                 整合測試              正式運行
    單元測試                UAT 驗收             對外服務
    Hot Reload             模擬生產              每日備份
```

| 環境 | 用途 | 基礎設施 | 資料 | 外部服務 |
| :--- | :--- | :--- | :--- | :--- |
| **Development** | 本地開發與除錯 | Docker Compose (local) | SQLite / PostgreSQL (local)，Mock 資料 | LINE Bot: 使用 ngrok 暫時隧道。Google AI: 開發帳號（設定用量上限） |
| **Staging** | 整合測試、UAT 驗收 | Docker Compose (VPS) | PostgreSQL (staging)，匿名化生產資料副本 | LINE Bot: 獨立的 Staging Channel。Google AI: 開發帳號 |
| **Production** | 正式運行環境 | Docker Compose (VPS/Cloud) | PostgreSQL (production)，每日備份（保留 30 天） | LINE Bot: 正式 Channel。Google AI: 正式帳號 |

**環境隔離原則：**
- 每個環境使用獨立的 `.env` 檔案，絕不共享密鑰
- Staging 與 Production 使用獨立的 LINE Channel
- 生產 API Key 僅存在於生產環境的密鑰管理中
- 開發環境使用 Google AI 帳號的用量上限 (usage cap) 防止誤用

### 1.2 部署拓撲圖 (Docker Compose)

以下為生產環境的 Docker Compose 部署拓撲：

```mermaid
graph TB
    subgraph "Host Machine (VPS / Cloud VM)"
        subgraph "Docker Network: smartlock-net"

            subgraph "Reverse Proxy"
                NGINX["Nginx<br/>---<br/>SSL Termination<br/>Reverse Proxy<br/>Static File Serving<br/>Rate Limiting<br/>---<br/>Port: 80, 443"]
            end

            subgraph "Application Tier"
                API1["FastAPI App<br/>(Worker 1)<br/>---<br/>Python 3.11 + Uvicorn<br/>Port: 8000"]
                API2["FastAPI App<br/>(Worker 2)<br/>---<br/>Python 3.11 + Uvicorn<br/>Port: 8001"]
            end

            subgraph "Frontend Tier (V2.0)"
                NEXT["Next.js 14+ App<br/>---<br/>SSR / Static<br/>Port: 3000"]
            end

            subgraph "Data Tier"
                PG["PostgreSQL 16<br/>+ pgvector 0.7+<br/>---<br/>Port: 5432<br/>Volume: pg_data"]
                RD["Redis 7<br/>---<br/>Port: 6379<br/>Volume: redis_data"]
            end

            subgraph "Utility"
                BACKUP["Backup CronJob<br/>---<br/>Daily pg_dump<br/>Volume: backup_data<br/>保留 30 天"]
            end
        end
    end

    subgraph "External"
        INTERNET["Internet<br/>(LINE Users / Admins / Technicians)"]
        LINE_SRV["LINE Messaging API"]
        GOOGLE_AI_SRV["Google AI API<br/>(Gemini 3 Pro + Embeddings)"]
        GOOGLE_MAPS["Google Maps API<br/>(V2.0)"]
    end

    INTERNET -- "HTTPS :443" --> NGINX
    LINE_SRV -- "Webhook POST :443" --> NGINX
    NGINX -- "Proxy Pass /api/* :8000" --> API1
    NGINX -- "Proxy Pass /api/* :8001" --> API2
    NGINX -- "Proxy Pass /* :3000" --> NEXT
    NEXT -- "API Call :8000" --> API1
    API1 -- "SQL :5432" --> PG
    API2 -- "SQL :5432" --> PG
    API1 -- "Cache :6379" --> RD
    API2 -- "Cache :6379" --> RD
    API1 -- "HTTPS" --> GOOGLE_AI_SRV
    API2 -- "HTTPS" --> GOOGLE_AI_SRV
    API1 -- "HTTPS" --> LINE_SRV
    API1 -- "HTTPS" --> GOOGLE_MAPS
    BACKUP -- "pg_dump :5432" --> PG
```

### 1.3 容器服務清單

| 服務名稱 | Image | 端口 | 環境變數 | Volume | 備註 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `nginx` | nginx:alpine | 80, 443 (external) | - | `./nginx/conf.d`, `./certs` | SSL 終止、反向代理、Rate Limiting |
| `api` (backend) | 自建 Dockerfile | 8000 (internal) | `DATABASE_URL`, `REDIS_URL`, `GOOGLE_API_KEY`, `LINE_CHANNEL_SECRET`, `LINE_CHANNEL_ACCESS_TOKEN`, `JWT_SECRET` | `./uploads` | 可用 `--scale api=2` 水平擴展 |
| `web` (frontend, V2.0) | 自建 Dockerfile | 3000 (internal) | `NEXT_PUBLIC_API_URL` | - | Next.js SSR |
| `postgres` | pgvector/pgvector:pg16 | 5432 (internal) | `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | `pg_data` | 啟用 pgvector extension |
| `redis` | redis:7-alpine | 6379 (internal) | - | `redis_data` | 持久化 appendonly |
| `backup` | postgres:16-alpine | - | - | `backup_data` | cron 排程 pg_dump，每日執行 |

### 1.4 網路與端口規劃

**Docker Network:** `smartlock-net` (bridge mode)

| 服務 | 內部端口 | 外部端口 | 說明 |
| :--- | :--- | :--- | :--- |
| Nginx | 80, 443 | 80, 443 | 唯一對外暴露的服務 |
| FastAPI Backend | 8000 | - (不對外) | 僅透過 Nginx 代理存取 |
| Next.js Frontend | 3000 | - (不對外) | 僅透過 Nginx 代理存取 |
| PostgreSQL | 5432 | - (不對外) | 僅 Docker 內部網路可存取 |
| Redis | 6379 | - (不對外) | 僅 Docker 內部網路可存取 |

**重要原則：** 生產環境中，僅 Nginx 的 80/443 端口對外暴露。資料庫與快取服務嚴禁對外暴露端口。

---

## 第 2 部分：CI/CD 流水線

### 2.1 流水線概覽

CI/CD 使用 GitHub Actions 實現，分為兩條流水線：

```mermaid
graph LR
    subgraph "Developer"
        DEV["git push<br/>to feature branch"]
    end

    subgraph "GitHub Actions Pipeline"
        subgraph "PR Pipeline (ci.yml)"
            LINT["Step 1: Lint<br/>---<br/>ruff check<br/>mypy type check"]
            TEST["Step 2: Test<br/>---<br/>pytest<br/>(unit + integration)<br/>coverage >= 70%"]
            BUILD["Step 3: Build<br/>---<br/>docker build<br/>image validation"]
        end

        subgraph "Main Pipeline (deploy.yml)"
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

### 2.2 ci.yml - 持續整合

**觸發條件：** 每次 `push` 或 `pull_request`

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: "3.11"
  NODE_VERSION: "20"

jobs:
  # ----- 後端 Lint -----
  lint-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          pip install ruff mypy
          pip install -r backend/requirements.txt

      - name: Run ruff check
        run: ruff check backend/src/

      - name: Run ruff format check
        run: ruff format --check backend/src/

      - name: Run mypy type check
        run: mypy backend/src/ --config-file backend/pyproject.toml

  # ----- 後端 Test -----
  test-backend:
    runs-on: ubuntu-latest
    needs: lint-backend
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_DB: smart_lock_test
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install -r backend/requirements-dev.txt

      - name: Run pytest with coverage
        env:
          DATABASE_URL: postgresql+asyncpg://test_user:test_password@localhost:5432/smart_lock_test
          REDIS_URL: redis://localhost:6379/0
          APP_ENV: testing
        run: |
          cd backend
          pytest tests/ -v --cov=src --cov-report=xml --cov-fail-under=70

      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: backend/coverage.xml

  # ----- 後端 Build -----
  build-backend:
    runs-on: ubuntu-latest
    needs: test-backend
    steps:
      - uses: actions/checkout@v4

      - name: Build Docker image
        run: docker build -t smartlock-api:ci-${{ github.sha }} ./backend

      - name: Verify image
        run: |
          docker run --rm smartlock-api:ci-${{ github.sha }} python -c "import smart_lock; print('OK')"

  # ----- 前端 Lint (V2.0) -----
  lint-frontend:
    runs-on: ubuntu-latest
    if: ${{ hashFiles('frontend/package.json') != '' }}
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Run ESLint
        run: cd frontend && npx eslint src/

      - name: Run TypeScript check
        run: cd frontend && npx tsc --noEmit

  # ----- 前端 Test (V2.0) -----
  test-frontend:
    runs-on: ubuntu-latest
    needs: lint-frontend
    if: ${{ hashFiles('frontend/package.json') != '' }}
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Run Jest tests
        run: cd frontend && npm test -- --coverage --watchAll=false
```

### 2.3 deploy.yml - 持續部署

**觸發條件：** merge 到 `main` 分支

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_PREFIX: ${{ github.repository }}

jobs:
  # ----- 版本標記 -----
  tag-version:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.new_tag }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Generate semantic version tag
        id: version
        uses: anothrNick/github-tag-action@1.71.0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          DEFAULT_BUMP: patch
          WITH_V: true

  # ----- 建置並推送映像檔 -----
  build-and-push:
    runs-on: ubuntu-latest
    needs: tag-version
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push backend image
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/api:${{ needs.tag-version.outputs.version }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/api:latest

      - name: Build and push frontend image (V2.0)
        if: ${{ hashFiles('frontend/Dockerfile') != '' }}
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/web:${{ needs.tag-version.outputs.version }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/web:latest

  # ----- 資料庫遷移 -----
  run-migrations:
    runs-on: ubuntu-latest
    needs: build-and-push
    steps:
      - name: Run Alembic migrations via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.DEPLOY_HOST }}
          username: ${{ secrets.DEPLOY_USER }}
          key: ${{ secrets.DEPLOY_SSH_KEY }}
          script: |
            cd /opt/smartlock
            docker compose run --rm api alembic upgrade head

  # ----- 部署到生產環境 -----
  deploy-production:
    runs-on: ubuntu-latest
    needs: run-migrations
    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.DEPLOY_HOST }}
          username: ${{ secrets.DEPLOY_USER }}
          key: ${{ secrets.DEPLOY_SSH_KEY }}
          script: |
            cd /opt/smartlock
            # 拉取最新映像檔
            docker compose -f docker-compose.prod.yml pull
            # 滾動重啟服務
            docker compose -f docker-compose.prod.yml up -d --remove-orphans
            # 清理舊映像檔
            docker image prune -f

  # ----- Smoke Test -----
  smoke-test:
    runs-on: ubuntu-latest
    needs: deploy-production
    steps:
      - name: Wait for services to stabilize
        run: sleep 30

      - name: Health check
        run: |
          HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
            https://${{ secrets.DEPLOY_HOST }}/health)
          if [ "$HTTP_STATUS" != "200" ]; then
            echo "Health check failed with status $HTTP_STATUS"
            exit 1
          fi
          echo "Health check passed: $HTTP_STATUS"

      - name: API validation
        run: |
          RESPONSE=$(curl -s https://${{ secrets.DEPLOY_HOST }}/api/v1/health)
          echo "API Response: $RESPONSE"
          echo "$RESPONSE" | jq -e '.status == "healthy"' || exit 1

      - name: Notify deployment result
        if: always()
        run: |
          if [ "${{ job.status }}" == "success" ]; then
            echo "Deployment successful - send success notification"
          else
            echo "Deployment failed - trigger rollback alert"
          fi
```

### 2.4 CI/CD 步驟詳細說明

| 步驟 | 觸發條件 | 工具 | 動作 | 失敗處理 |
| :--- | :--- | :--- | :--- | :--- |
| **Lint** | PR opened / push | `ruff`, `mypy` | 程式碼風格檢查、型別檢查 | 阻擋 PR merge |
| **Test** | PR opened / push | `pytest`, `pytest-cov` | 單元測試 + 整合測試，覆蓋率門檻 70% | 阻擋 PR merge |
| **Build** | PR opened / push | `docker build` | 驗證 Docker Image 可成功建置 | 阻擋 PR merge |
| **Tag** | merge to main | GitHub Actions | 自動生成語義化版本 Tag (SemVer) | 手動介入 |
| **Push Image** | tag created | Container Registry | 推送帶版本 Tag 的 Image | 重試 3 次 |
| **Migrations** | image pushed | Alembic via SSH | 執行 `alembic upgrade head` | 手動介入，不繼續部署 |
| **Deploy** | migrations done | SSH + docker-compose | `docker compose pull && docker compose up -d` | 回滾至前一版本 |
| **Smoke Test** | deploy completed | curl + custom script | 健康檢查端點、關鍵 API 驗證 | 自動回滾 + 告警通知 |

---

## 第 3 部分：部署檢查清單

### 3.1 部署前檢查

| 類別 | 檢查項目 | 負責人 |
| :--- | :--- | :--- |
| **程式碼品質** | [ ] Code Review 已完成並通過 | 開發者 |
| **程式碼品質** | [ ] 所有測試通過（單元測試、整合測試） | CI 自動化 |
| **程式碼品質** | [ ] 程式碼覆蓋率 >= 70% | CI 自動化 |
| **程式碼品質** | [ ] ruff lint + mypy type check 通過 | CI 自動化 |
| **安全性** | [ ] 無敏感資訊提交至版本控制 (`.env`, API keys) | 開發者 |
| **安全性** | [ ] Docker Image 安全掃描完成 | CI 自動化 |
| **資料庫** | [ ] Alembic migration 腳本已準備（如需要） | 開發者 |
| **資料庫** | [ ] Migration 已在 Staging 環境驗證 | 開發者 |
| **資料庫** | [ ] 生產資料庫已執行備份 | DevOps |
| **外部服務** | [ ] LINE Channel 配置正確（Webhook URL 等） | DevOps |
| **外部服務** | [ ] Google AI API Key 有效且額度充足 | DevOps |
| **文件** | [ ] 回滾計畫已文件化 | 開發者 |
| **溝通** | [ ] 已通知團隊即將部署 | 技術負責人 |

### 3.2 部署中監控

| 類別 | 檢查項目 | 負責人 |
| :--- | :--- | :--- |
| **流程** | [ ] 監控 GitHub Actions 部署進度 | DevOps |
| **健康檢查** | [ ] `/health` 端點回傳 200 | 自動化 |
| **日誌** | [ ] 檢查應用程式日誌無異常錯誤 | DevOps |
| **指標** | [ ] 監控 CPU / 記憶體使用率無異常飆升 | DevOps |
| **資料庫** | [ ] 確認資料庫連線正常 | 自動化 |
| **快取** | [ ] 確認 Redis 連線正常 | 自動化 |
| **外部服務** | [ ] LINE Webhook 可正常接收事件 | DevOps |

### 3.3 部署後驗證

| 類別 | 檢查項目 | 負責人 |
| :--- | :--- | :--- |
| **功能驗證** | [ ] Smoke Test 全部通過 | 自動化 |
| **功能驗證** | [ ] LINE Bot 可正常回覆訊息 | QA |
| **功能驗證** | [ ] Admin Panel 可正常登入與操作 | QA |
| **效能** | [ ] P95 API 延遲 < 2s（非 LLM 端點） | 監控系統 |
| **效能** | [ ] P95 LLM 延遲 < 10s | 監控系統 |
| **效能** | [ ] 錯誤率維持在正常範圍內 | 監控系統 |
| **資料** | [ ] 資料庫 migration 已成功套用 | DevOps |
| **文件** | [ ] 部署版本號已記錄 | DevOps |
| **文件** | [ ] 如有異常，已記錄並排定改善 | 技術負責人 |

---

## 第 4 部分：部署策略

### 4.1 Blue-Green 部署 (生產環境)

生產環境採用 Blue-Green 部署策略，確保零停機時間與快速回滾能力。

```
                    ┌─────────────────────────────────┐
                    │          Nginx (Router)          │
                    │   upstream: blue / green toggle  │
                    └────────────┬────────────────────┘
                                 │
                    ┌────────────┴────────────────────┐
                    │                                  │
           ┌───────▼───────┐              ┌───────────▼───────┐
           │  Blue Env     │              │  Green Env        │
           │  (Current)    │              │  (New Version)    │
           │               │              │                   │
           │  api:v1.2.0   │              │  api:v1.3.0       │
           │  web:v1.2.0   │              │  web:v1.3.0       │
           └───────────────┘              └───────────────────┘
```

**Blue-Green 部署流程：**

```bash
#!/bin/bash
# scripts/deploy-blue-green.sh

set -e

DEPLOY_DIR="/opt/smartlock"
CURRENT_ENV=$(cat ${DEPLOY_DIR}/.current-env 2>/dev/null || echo "blue")

if [ "$CURRENT_ENV" = "blue" ]; then
  NEW_ENV="green"
else
  NEW_ENV="blue"
fi

echo "=== 當前環境: ${CURRENT_ENV}, 部署目標: ${NEW_ENV} ==="

# Step 1: 拉取新版映像檔
echo "--- Step 1: 拉取新版映像檔 ---"
docker compose -f docker-compose.${NEW_ENV}.yml pull

# Step 2: 啟動新環境
echo "--- Step 2: 啟動新環境 (${NEW_ENV}) ---"
docker compose -f docker-compose.${NEW_ENV}.yml up -d

# Step 3: 等待服務就緒
echo "--- Step 3: 等待服務就緒 ---"
sleep 15
for i in $(seq 1 10); do
  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:800${NEW_ENV_PORT}/health)
  if [ "$HTTP_STATUS" = "200" ]; then
    echo "新環境健康檢查通過"
    break
  fi
  echo "等待中... (${i}/10)"
  sleep 5
done

if [ "$HTTP_STATUS" != "200" ]; then
  echo "錯誤：新環境健康檢查失敗，中止部署"
  docker compose -f docker-compose.${NEW_ENV}.yml down
  exit 1
fi

# Step 4: 切換 Nginx 流量至新環境
echo "--- Step 4: 切換流量至 ${NEW_ENV} ---"
cp nginx/conf.d/upstream-${NEW_ENV}.conf nginx/conf.d/upstream-active.conf
docker compose exec nginx nginx -s reload

# Step 5: 驗證切換成功
echo "--- Step 5: 驗證切換 ---"
sleep 5
HEALTH=$(curl -s https://your-domain.com/health)
echo "Health response: ${HEALTH}"

# Step 6: 關閉舊環境
echo "--- Step 6: 關閉舊環境 (${CURRENT_ENV}) ---"
docker compose -f docker-compose.${CURRENT_ENV}.yml down

# Step 7: 記錄當前環境
echo "${NEW_ENV}" > ${DEPLOY_DIR}/.current-env
echo "=== 部署完成: ${NEW_ENV} 已上線 ==="
```

### 4.2 滾動部署 (Staging 環境)

Staging 環境採用簡化的滾動部署：

```bash
#!/bin/bash
# scripts/deploy-staging.sh

set -e

DEPLOY_DIR="/opt/smartlock-staging"

cd ${DEPLOY_DIR}

# 備份當前版本資訊
docker compose images > .previous-versions.txt

# 拉取最新映像檔
docker compose pull

# 滾動重啟（先啟新，後停舊）
docker compose up -d --remove-orphans

# 等待就緒並驗證
sleep 15
curl -f http://localhost/health || {
  echo "部署失敗，執行回滾"
  docker compose down
  docker compose up -d  # 使用本地快取的舊映像
  exit 1
}

echo "Staging 部署完成"
```

### 4.3 首次部署流程

首次部署需要額外的初始化步驟：

```bash
#!/bin/bash
# scripts/initial-deploy.sh

set -e

DEPLOY_DIR="/opt/smartlock"

# Step 1: 建立目錄結構
mkdir -p ${DEPLOY_DIR}/{nginx/conf.d,certs,backups,uploads,logs}

# Step 2: 複製設定檔
cp docker-compose.prod.yml ${DEPLOY_DIR}/docker-compose.yml
cp .env.production ${DEPLOY_DIR}/.env
cp -r nginx/ ${DEPLOY_DIR}/nginx/

# Step 3: 設定 SSL 憑證（使用 Let's Encrypt）
certbot certonly --standalone -d your-domain.com
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ${DEPLOY_DIR}/certs/
cp /etc/letsencrypt/live/your-domain.com/privkey.pem ${DEPLOY_DIR}/certs/

# Step 4: 啟動服務
cd ${DEPLOY_DIR}
docker compose up -d

# Step 5: 等待 PostgreSQL 就緒
echo "等待 PostgreSQL 啟動..."
sleep 10
docker compose exec postgres pg_isready -U smartlock

# Step 6: 執行資料庫初始化
docker compose exec api alembic upgrade head

# Step 7: 載入初始 RAG 知識庫資料（如有需要）
docker compose exec api python -m smart_lock.scripts.seed_knowledge_base

# Step 8: 設定自動備份 CronJob
(crontab -l 2>/dev/null; echo "0 3 * * * cd ${DEPLOY_DIR} && ./scripts/backup.sh >> ${DEPLOY_DIR}/logs/backup.log 2>&1") | crontab -

# Step 9: 驗證
curl -f https://your-domain.com/health
echo "首次部署完成"
```

---

## 第 5 部分：監控與告警

### 5.1 應用程式指標

| 指標類別 | 指標名稱 | 類型 | 目標值 | 說明 |
| :--- | :--- | :--- | :--- | :--- |
| **API 效能** | `api_request_duration_seconds` | Histogram | P95 < 2s | REST API 請求延遲分佈（不含 LLM） |
| **API 效能** | `api_request_total` | Counter | - | API 請求總數（按 method, path, status） |
| **LLM 效能** | `llm_call_duration_seconds` | Histogram | P95 < 10s | LLM API 呼叫延遲 |
| **LLM 效能** | `llm_token_usage_total` | Counter | - | Token 使用量（按 model, type） |
| **LLM 成本** | `llm_cost_usd_total` | Counter | - | LLM 累計花費（USD） |
| **解決率** | `resolution_total` | Counter | - | 問題解決次數（按 level: L1/L2/L3） |
| **解決率** | `resolution_success_rate` | Gauge | L1 >= 40% | 各層解決成功率 |
| **知識庫** | `knowledge_base_entries_total` | Gauge | - | CaseEntry 和 ManualChunk 總數 |
| **LINE** | `webhook_processing_duration_seconds` | Histogram | P95 < 1s | LINE Webhook 處理時間（必須 < 1s 回傳 200） |

**指標實現：** V1.0 使用 FastAPI middleware 收集基礎 API 指標，提供 `/metrics` 端點。可選接入 Prometheus + Grafana。

**健康檢查端點：**

```json
// GET /health
{
  "status": "healthy",
  "version": "1.2.0",
  "timestamp": "2026-02-25T10:30:00Z",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "line_api": "ok",
    "google_ai_api": "ok"
  }
}
```

### 5.2 基礎設施指標

| 指標 | 監控目標 | 告警閾值 | 說明 |
| :--- | :--- | :--- | :--- |
| **CPU 使用率** | 所有容器 | > 80% 持續 5 分鐘 | Docker stats 或 cAdvisor |
| **記憶體使用率** | 所有容器 | > 85% 持續 5 分鐘 | 重點監控 FastAPI 與 PostgreSQL |
| **磁碟使用率** | Host Machine | > 85% | 含 pg_data, redis_data, backup_data |
| **網路 I/O** | Nginx | 異常流量 spike | 可能是 DDoS 攻擊徵兆 |
| **容器狀態** | 所有容器 | 非 running 狀態 | Docker Health Check |
| **PostgreSQL 連線池** | api 容器 | > 90% 使用率 | asyncpg pool size 配置 |
| **Redis 記憶體** | redis 容器 | > 80% maxmemory | 監控 session 與 cache 使用 |

**基礎設施監控腳本：**

```bash
#!/bin/bash
# scripts/monitor-infra.sh
# 由 cron 每 5 分鐘執行一次

DEPLOY_DIR="/opt/smartlock"
LOG_FILE="${DEPLOY_DIR}/logs/monitor.log"
ALERT_WEBHOOK_URL="${ALERT_WEBHOOK_URL:-}"

check_disk_usage() {
  DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
  if [ "$DISK_USAGE" -gt 85 ]; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) ALERT: Disk usage at ${DISK_USAGE}%" >> ${LOG_FILE}
    # 觸發告警通知
  fi
}

check_container_health() {
  UNHEALTHY=$(docker ps --filter "health=unhealthy" --format "{{.Names}}" 2>/dev/null)
  if [ -n "$UNHEALTHY" ]; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) ALERT: Unhealthy containers: ${UNHEALTHY}" >> ${LOG_FILE}
    # 觸發告警通知
  fi
}

check_disk_usage
check_container_health
```

### 5.3 業務指標

| 指標 | 說明 | 監控頻率 |
| :--- | :--- | :--- |
| **活躍對話數** | `active_conversations` — 當前進行中的 LINE 對話 Session | 即時 |
| **問題解決率** | L1/L2 自動解決 vs L3 人工升級的比率 | 每日統計 |
| **知識庫命中率** | L1 向量搜尋命中率（相似度 >= 0.85 的比率） | 每日統計 |
| **LLM 月度花費** | Google AI API 累計費用 | 每日追蹤，月度匯總 |
| **Webhook 回應時間** | LINE Webhook 接收到回傳 200 的時間（必須 < 1 秒） | 即時 |
| **SOP 生成量** | SOP Generator 自動生成的草稿數量 | 每週統計 |
| **V2.0 工單量** | 工單建立/完成數量（按 status 分類） | 每日統計 |
| **V2.0 技師媒合時間** | 從工單建立到技師接單的平均時間 | 即時 |

### 5.4 告警配置

| 告警名稱 | 條件 | 嚴重度 | 通知管道 | 回應 SLA |
| :--- | :--- | :--- | :--- | :--- |
| API 高延遲 | P95 > 5s 持續 5 分鐘 | P2 - Warning | LINE 群組通知 | 30 分鐘內回應 |
| API 錯誤率飆升 | 5xx 比率 > 5% 持續 3 分鐘 | P1 - Critical | LINE 群組通知 + 電話 | 15 分鐘內回應 |
| LLM 呼叫失敗 | 連續失敗 > 3 次 | P1 - Critical | LINE 群組通知 | 15 分鐘內回應 |
| 資料庫連線耗盡 | 連線池使用率 > 90% | P2 - Warning | LINE 群組通知 | 30 分鐘內回應 |
| 磁碟使用率過高 | > 85% | P2 - Warning | LINE 群組通知 | 1 小時內回應 |
| 備份失敗 | 每日備份未在預期時間完成 | P1 - Critical | LINE 群組通知 + Email | 1 小時內回應 |
| 容器異常停止 | 任何容器非 running 狀態 | P1 - Critical | LINE 群組通知 + 電話 | 15 分鐘內回應 |
| LINE Webhook 逾時 | 處理時間 > 1s 比率超過 10% | P2 - Warning | LINE 群組通知 | 30 分鐘內回應 |
| LLM 月度費用超標 | 累計費用超過預算 80% | P3 - Info | Email | 1 個工作天內回應 |

**告警配置範例（結構化格式）：**

```yaml
# configs/alerts.yml
alerts:
  - name: HighErrorRate
    description: "API 5xx 錯誤率飆升"
    condition: "error_rate_5xx > 0.05 for 3m"
    severity: critical
    actions:
      - type: line_notify
        target: ops-group
      - type: phone_call
        target: on-call-engineer

  - name: HighAPILatency
    description: "API 回應延遲過高"
    condition: "api_request_duration_seconds_p95 > 5 for 5m"
    severity: warning
    actions:
      - type: line_notify
        target: ops-group

  - name: LLMCallFailure
    description: "LLM API 連續呼叫失敗"
    condition: "llm_consecutive_failures > 3"
    severity: critical
    actions:
      - type: line_notify
        target: ops-group

  - name: WebhookTimeout
    description: "LINE Webhook 處理超時"
    condition: "webhook_duration_seconds_p95 > 1 for 5m"
    severity: warning
    actions:
      - type: line_notify
        target: ops-group

  - name: BackupFailure
    description: "每日資料庫備份失敗"
    condition: "backup_job_status != success"
    severity: critical
    actions:
      - type: line_notify
        target: ops-group
      - type: email
        target: tech-lead@company.com
```

### 5.5 日誌管理

**日誌規範：**

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
  "timestamp": "2026-02-25T10:30:45.123+08:00",
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

**Docker 日誌配置：**

```yaml
# docker-compose.prod.yml 中的日誌配置
services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"
        tag: "smartlock-api"
```

---

## 第 6 部分：回滾程序

### 6.1 自動回滾觸發條件

以下條件將在 Smoke Test 階段自動觸發回滾：

| 條件 | 檢測方式 | 回滾動作 |
| :--- | :--- | :--- |
| 健康檢查失敗 | `/health` 回傳非 200 | 自動回滾至前一版本 |
| API 端點驗證失敗 | `/api/v1/health` 回傳異常 | 自動回滾至前一版本 |
| 錯誤率飆升 | 5xx 比率 > 10%（部署後 5 分鐘內） | 自動回滾至前一版本 |
| 資料庫連線失敗 | 健康檢查中 database 狀態非 ok | 自動回滾至前一版本 |

### 6.2 手動回滾流程

```bash
#!/bin/bash
# scripts/rollback.sh
# 用法: ./scripts/rollback.sh [version]

set -e

DEPLOY_DIR="/opt/smartlock"
ROLLBACK_VERSION=${1:-""}

cd ${DEPLOY_DIR}

echo "=== 開始回滾程序 ==="

# Step 1: 確認回滾版本
if [ -z "$ROLLBACK_VERSION" ]; then
  echo "未指定版本，回滾至前一版本..."
  # 讀取前一版本紀錄
  ROLLBACK_VERSION=$(cat .previous-version 2>/dev/null)
  if [ -z "$ROLLBACK_VERSION" ]; then
    echo "錯誤：找不到前一版本紀錄，請手動指定版本號"
    echo "用法: ./scripts/rollback.sh v1.2.0"
    exit 1
  fi
fi

echo "回滾目標版本: ${ROLLBACK_VERSION}"

# Step 2: 拉取指定版本映像檔
echo "--- Step 2: 拉取版本 ${ROLLBACK_VERSION} 映像檔 ---"
export IMAGE_TAG=${ROLLBACK_VERSION}
docker compose -f docker-compose.prod.yml pull

# Step 3: 停止當前服務
echo "--- Step 3: 停止當前服務 ---"
docker compose -f docker-compose.prod.yml down

# Step 4: 啟動回滾版本
echo "--- Step 4: 啟動回滾版本 ---"
docker compose -f docker-compose.prod.yml up -d

# Step 5: 等待並驗證
echo "--- Step 5: 驗證回滾結果 ---"
sleep 15
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://your-domain.com/health)
if [ "$HTTP_STATUS" = "200" ]; then
  echo "回滾成功: 健康檢查通過"
else
  echo "嚴重錯誤: 回滾後健康檢查仍然失敗 (HTTP ${HTTP_STATUS})"
  echo "請立即手動介入排查"
  exit 1
fi

# Step 6: 記錄回滾事件
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) ROLLBACK to ${ROLLBACK_VERSION}" >> ${DEPLOY_DIR}/logs/deploy.log

echo "=== 回滾完成 ==="
```

### 6.3 資料庫回滾

**Alembic Migration 回滾：**

```bash
# 回滾最近一次 migration
docker compose exec api alembic downgrade -1

# 回滾到指定版本
docker compose exec api alembic downgrade <revision_id>

# 查看 migration 歷史
docker compose exec api alembic history --verbose

# 查看當前版本
docker compose exec api alembic current
```

**從備份還原資料庫（最後手段）：**

```bash
#!/bin/bash
# scripts/restore-database.sh
# 用法: ./scripts/restore-database.sh <backup_file>

set -e

BACKUP_FILE=$1
DEPLOY_DIR="/opt/smartlock"

if [ -z "$BACKUP_FILE" ]; then
  echo "用法: ./scripts/restore-database.sh backups/smart_lock_20260225_030000.sql.gz"
  echo ""
  echo "可用備份檔案："
  ls -la ${DEPLOY_DIR}/backups/*.sql.gz | tail -10
  exit 1
fi

echo "警告：此操作將覆蓋生產資料庫！"
echo "備份檔案: ${BACKUP_FILE}"
read -p "確認繼續？(yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
  echo "操作取消"
  exit 0
fi

# Step 1: 停止應用服務（保持資料庫運行）
echo "--- 停止應用服務 ---"
cd ${DEPLOY_DIR}
docker compose stop api web

# Step 2: 還原資料庫
echo "--- 還原資料庫 ---"
gunzip -c ${BACKUP_FILE} | docker compose exec -T postgres psql -U smartlock -d smart_lock

# Step 3: 重新啟動應用服務
echo "--- 重新啟動應用服務 ---"
docker compose start api web

# Step 4: 驗證
sleep 10
curl -f https://your-domain.com/health && echo "還原成功" || echo "還原後驗證失敗"
```

**重要提醒：**
- 資料庫回滾可能導致資料丟失，務必在回滾前確認影響範圍
- 若 migration 包含不可逆操作（如 DROP COLUMN），則無法使用 `alembic downgrade`，須從備份還原
- 建議在執行 migration 前，先在 Staging 環境驗證 upgrade 與 downgrade 都能正常執行

---

## 第 7 部分：基礎設施即程式碼

### 7.1 Docker Compose 配置

#### 開發環境 (docker-compose.yml)

```yaml
# docker-compose.yml - Development
version: "3.8"

services:
  # ----- FastAPI 後端 -----
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: development
    ports:
      - "8000:8000"
    volumes:
      - ./backend/src:/app/src  # Hot reload
      - ./uploads:/app/uploads
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: uvicorn smart_lock.main:app --host 0.0.0.0 --port 8000 --reload
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ----- Next.js 前端 (V2.0) -----
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: development
    ports:
      - "3000:3000"
    volumes:
      - ./frontend/src:/app/src  # Hot reload
    env_file: .env
    depends_on:
      - backend
    command: npm run dev
    profiles:
      - v2  # 使用 --profile v2 啟動

  # ----- PostgreSQL 16 + pgvector -----
  db:
    image: pgvector/pgvector:pg16
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./SQL/Schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-smart_lock}
      POSTGRES_USER: ${POSTGRES_USER:-smartlock}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-devpassword}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-smartlock} -d ${POSTGRES_DB:-smart_lock}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ----- Redis -----
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
  redisdata:

networks:
  default:
    name: smartlock-net
```

#### 生產環境 (docker-compose.prod.yml)

```yaml
# docker-compose.prod.yml - Production
version: "3.8"

services:
  # ----- Nginx 反向代理 -----
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
      - ./frontend-static:/usr/share/nginx/html:ro
    depends_on:
      - backend
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "20m"
        max-file: "3"

  # ----- FastAPI 後端 -----
  backend:
    image: ${REGISTRY:-ghcr.io}/${IMAGE_PREFIX:-smartlock}/api:${IMAGE_TAG:-latest}
    expose:
      - "8000"
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./uploads:/app/uploads
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: "1.0"
          memory: 1G
        reservations:
          cpus: "0.5"
          memory: 512M
    restart: always
    command: uvicorn smart_lock.main:app --host 0.0.0.0 --port 8000 --workers 2
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"
        tag: "smartlock-api"

  # ----- Next.js 前端 (V2.0) -----
  web:
    image: ${REGISTRY:-ghcr.io}/${IMAGE_PREFIX:-smartlock}/web:${IMAGE_TAG:-latest}
    expose:
      - "3000"
    env_file: .env
    depends_on:
      - backend
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "20m"
        max-file: "3"
    profiles:
      - v2  # V2.0 階段啟用

  # ----- PostgreSQL 16 + pgvector -----
  db:
    image: pgvector/pgvector:pg16
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./configs/postgresql.conf:/etc/postgresql/postgresql.conf:ro
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    command: postgres -c config_file=/etc/postgresql/postgresql.conf
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 2G
        reservations:
          cpus: "1.0"
          memory: 1G
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"

  # ----- Redis -----
  redis:
    image: redis:7-alpine
    volumes:
      - redisdata:/data
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    restart: always
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          cpus: "0.5"
          memory: 512M
    logging:
      driver: "json-file"
      options:
        max-size: "20m"
        max-file: "3"

  # ----- 資料庫備份 -----
  backup:
    image: postgres:16-alpine
    volumes:
      - ./backups:/backups
      - ./scripts/backup.sh:/scripts/backup.sh:ro
    environment:
      PGHOST: db
      PGUSER: ${POSTGRES_USER}
      PGPASSWORD: ${POSTGRES_PASSWORD}
      PGDATABASE: ${POSTGRES_DB}
    depends_on:
      db:
        condition: service_healthy
    entrypoint: /bin/sh
    command: >
      -c "
      echo '0 3 * * * /scripts/backup.sh' | crontab - &&
      crond -f -l 2
      "
    restart: always

volumes:
  pgdata:
    driver: local
  redisdata:
    driver: local

networks:
  default:
    name: smartlock-net
```

### 7.2 Nginx 反向代理配置

#### 主配置 (nginx/nginx.conf)

```nginx
# nginx/nginx.conf

user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    multi_accept on;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # JSON 格式日誌
    log_format json_combined escape=json
        '{'
            '"time":"$time_iso8601",'
            '"remote_addr":"$remote_addr",'
            '"request":"$request",'
            '"status":$status,'
            '"body_bytes_sent":$body_bytes_sent,'
            '"request_time":$request_time,'
            '"upstream_response_time":"$upstream_response_time",'
            '"http_user_agent":"$http_user_agent",'
            '"http_x_forwarded_for":"$http_x_forwarded_for"'
        '}';

    access_log /var/log/nginx/access.log json_combined;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 50M;  # PDF 上傳大小限制

    # Gzip 壓縮
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    include /etc/nginx/conf.d/*.conf;
}
```

#### 站台配置 (nginx/conf.d/default.conf)

```nginx
# nginx/conf.d/default.conf

# Backend upstream (支援多 worker)
upstream backend {
    least_conn;
    server backend:8000;
    # 若使用 --scale backend=2，Docker Compose 會自動負載均衡
}

# Frontend upstream (V2.0)
upstream frontend {
    server web:3000;
}

# HTTP -> HTTPS 重導
server {
    listen 80;
    server_name your-domain.com;

    # Let's Encrypt 驗證用
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS 主站台
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 憑證
    ssl_certificate     /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;

    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=30r/s;
    limit_req_zone $binary_remote_addr zone=webhook_limit:10m rate=50r/s;

    # ----- LINE Webhook -----
    location /webhook {
        limit_req zone=webhook_limit burst=100 nodelay;

        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Webhook 必須快速回應
        proxy_read_timeout 5s;
        proxy_connect_timeout 2s;
    }

    # ----- Backend REST API -----
    location /api/ {
        limit_req zone=api_limit burst=50 nodelay;

        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # LLM 呼叫可能較慢
        proxy_read_timeout 30s;
        proxy_connect_timeout 5s;
    }

    # ----- Health Check -----
    location /health {
        proxy_pass http://backend;
        proxy_set_header Host $host;

        # 不做 Rate Limiting
        access_log off;
    }

    # ----- FastAPI 文件 (僅非生產環境) -----
    location /docs {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        # 生產環境建議關閉：deny all;
    }

    location /openapi.json {
        proxy_pass http://backend;
        proxy_set_header Host $host;
    }

    # ----- Metrics 端點 -----
    location /metrics {
        proxy_pass http://backend;
        proxy_set_header Host $host;

        # 僅允許內部存取
        allow 10.0.0.0/8;
        allow 172.16.0.0/12;
        allow 192.168.0.0/16;
        deny all;
    }

    # ----- Frontend (V2.0) -----
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支援 (V2.0 即時通知)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 7.3 Dockerfile 配置

#### 後端 Dockerfile (backend/Dockerfile)

```dockerfile
# backend/Dockerfile

# ----- Stage 1: Base -----
FROM python:3.11-slim as base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# ----- Stage 2: Dependencies -----
FROM base as dependencies

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ----- Stage 3: Development -----
FROM dependencies as development

COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "smart_lock.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ----- Stage 4: Production -----
FROM dependencies as production

# 建立非 root 使用者
RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY src/ /app/src/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/alembic.ini
COPY configs/ /app/configs/

# 設定目錄權限
RUN mkdir -p /app/uploads && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "smart_lock.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

#### 前端 Dockerfile (frontend/Dockerfile) — V2.0

```dockerfile
# frontend/Dockerfile

# ----- Stage 1: Dependencies -----
FROM node:20-alpine as dependencies

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --only=production

# ----- Stage 2: Development -----
FROM node:20-alpine as development

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"]

# ----- Stage 3: Build -----
FROM node:20-alpine as builder

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# ----- Stage 4: Production -----
FROM node:20-alpine as production

WORKDIR /app

# 建立非 root 使用者
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000
ENV PORT=3000 \
    HOSTNAME="0.0.0.0"

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD wget -q --spider http://localhost:3000/ || exit 1

CMD ["node", "server.js"]
```

---

## 第 8 部分：部署安全性

### 8.1 密鑰管理

| 密鑰 | 儲存方式 | 存取方式 | 輪替策略 |
| :--- | :--- | :--- | :--- |
| `GOOGLE_API_KEY` | `.env` 檔案（不入版本控制）/ GitHub Secrets | 環境變數 | 每季度輪替 |
| `LINE_CHANNEL_SECRET` | `.env` 檔案 / GitHub Secrets | 環境變數 | LINE 後台設定，按需輪替 |
| `LINE_CHANNEL_ACCESS_TOKEN` | `.env` 檔案 / GitHub Secrets | 環境變數 | LINE 後台設定，按需輪替 |
| `JWT_SECRET_KEY` | `.env` 檔案 / GitHub Secrets | 環境變數 | 每季度輪替 |
| `DATABASE_URL` | `.env` 檔案 / GitHub Secrets | 環境變數 | 密碼每季度輪替 |
| `REDIS_URL` | `.env` 檔案 / GitHub Secrets | 環境變數 | 按需設定 |
| `DEPLOY_SSH_KEY` | GitHub Secrets | CI/CD 部署專用 | 每半年輪替 |

**密鑰安全規範：**

- [ ] `.env` 檔案已加入 `.gitignore`，絕不提交至版本控制
- [ ] `.env.example` 提供所有環境變數的範本（值為佔位符）
- [ ] 生產環境密鑰與開發/Staging 環境嚴格隔離
- [ ] GitHub Secrets 用於 CI/CD 流水線中的密鑰注入
- [ ] 定期輪替所有密鑰（至少每季度一次）
- [ ] Google AI API 設定用量上限 (usage cap) 以防誤用或洩露

### 8.2 網路安全

**防火牆規則 (Host Machine)：**

```bash
# UFW 防火牆配置
# 僅開放必要端口
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH（建議限制來源 IP）
sudo ufw allow 80/tcp    # HTTP (Nginx)
sudo ufw allow 443/tcp   # HTTPS (Nginx)
sudo ufw enable

# 限制 SSH 登入來源（建議）
sudo ufw allow from <your-office-ip> to any port 22
sudo ufw deny 22/tcp
```

**Docker 網路隔離：**
- 所有服務在 `smartlock-net` bridge 網路中通訊
- 僅 Nginx 容器的 80/443 端口映射至 Host
- PostgreSQL 與 Redis 不對外暴露端口
- 容器間通訊使用 Docker DNS 服務名稱（如 `db:5432`）

**Rate Limiting：**
- Nginx 層：IP 級別限流（API: 30 req/s, Webhook: 50 req/s）
- 應用層：Redis 實現用戶級別限流（防止單一用戶濫用）

### 8.3 容器安全

- [ ] 使用官方或經過驗證的 Docker 映像檔（`python:3.11-slim`, `nginx:alpine`, `redis:7-alpine`）
- [ ] 生產環境容器以非 root 使用者運行（`appuser`, `nextjs`）
- [ ] 多階段建構 (Multi-stage Build) 減少最終映像檔大小與攻擊面
- [ ] 定期更新基礎映像檔以修補安全漏洞
- [ ] Volume 使用唯讀掛載 (`:ro`) 限制不必要的寫入權限
- [ ] 設定容器資源限制（CPU, Memory）防止單一容器耗盡主機資源

### 8.4 外部服務安全

| 外部服務 | 安全措施 |
| :--- | :--- |
| **LINE Messaging API** | 每次 Webhook 請求驗證 HMAC-SHA256 簽章；拒絕簽章不匹配的請求 |
| **Google Gemini 3 Pro API** | API Key 透過環境變數注入；設定每日/每月用量上限；Prompt Injection 防護（System Prompt 硬化、輸出過濾） |
| **Google Maps API (V2.0)** | API Key 限制 HTTP Referrer；設定每日呼叫上限 |
| **SSL/TLS** | 使用 Let's Encrypt 自動更新 SSL 憑證；強制 HTTPS；僅啟用 TLS 1.2+ |

---

## 第 9 部分：運維手冊 (Runbook)

### 9.1 資料庫遷移

**場景：** 部署新版本時需要更新資料庫 Schema

```bash
# === 資料庫遷移標準流程 ===

# Step 1: 確認當前 migration 版本
docker compose exec api alembic current

# Step 2: 查看待執行的 migration
docker compose exec api alembic history --verbose

# Step 3: 備份資料庫（執行 migration 前必做）
./scripts/backup.sh

# Step 4: 在 Staging 先行驗證
# (在 staging 環境中)
docker compose exec api alembic upgrade head
# 驗證功能正常後繼續

# Step 5: 在 Production 執行 migration
docker compose exec api alembic upgrade head

# Step 6: 驗證結果
docker compose exec api alembic current
docker compose exec postgres psql -U smartlock -d smart_lock -c "\dt"

# Step 7: 如需回滾
docker compose exec api alembic downgrade -1
```

**注意事項：**
- 生產環境執行 migration 前必須先備份資料庫
- 避免在高流量時段執行包含 ALTER TABLE 的 migration
- 大型 migration（如新增索引）建議使用 `CREATE INDEX CONCURRENTLY`
- pgvector HNSW 索引的建立可能耗時較長，建議安排在低流量時段

### 9.2 手動備份

**場景：** 排程外的緊急備份，或部署前的安全備份

```bash
#!/bin/bash
# scripts/backup.sh
# 用法: ./scripts/backup.sh [backup_name]

set -e

DEPLOY_DIR="/opt/smartlock"
BACKUP_DIR="${DEPLOY_DIR}/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME=${1:-"smart_lock_${TIMESTAMP}"}
BACKUP_FILE="${BACKUP_DIR}/${BACKUP_NAME}.sql.gz"
RETENTION_DAYS=30

# 確保備份目錄存在
mkdir -p ${BACKUP_DIR}

echo "=== 開始資料庫備份 ==="
echo "備份檔案: ${BACKUP_FILE}"

# 執行 pg_dump 並壓縮
docker compose exec -T db pg_dump \
  -U ${POSTGRES_USER:-smartlock} \
  -d ${POSTGRES_DB:-smart_lock} \
  --format=custom \
  --verbose \
  2>> ${DEPLOY_DIR}/logs/backup.log \
  | gzip > ${BACKUP_FILE}

# 驗證備份檔案
FILESIZE=$(stat -f%z "${BACKUP_FILE}" 2>/dev/null || stat -c%s "${BACKUP_FILE}" 2>/dev/null)
if [ "$FILESIZE" -lt 1024 ]; then
  echo "錯誤：備份檔案過小 (${FILESIZE} bytes)，可能備份失敗"
  exit 1
fi

echo "備份完成: ${BACKUP_FILE} (${FILESIZE} bytes)"

# 清理過期備份（保留 30 天）
echo "--- 清理 ${RETENTION_DAYS} 天前的舊備份 ---"
find ${BACKUP_DIR} -name "*.sql.gz" -mtime +${RETENTION_DAYS} -delete

# 列出現有備份
echo "--- 現有備份檔案 ---"
ls -lh ${BACKUP_DIR}/*.sql.gz 2>/dev/null | tail -10

echo "=== 備份流程結束 ==="
```

### 9.3 服務重啟

**場景：** 服務異常需要重啟

```bash
# === 重啟單一服務 ===

# 重啟 FastAPI 後端
docker compose restart backend

# 重啟 Nginx
docker compose restart nginx

# 重啟 Redis（注意：會清除非持久化的快取資料）
docker compose restart redis

# === 重啟全部服務 ===

# 優雅重啟（推薦）
docker compose down && docker compose -f docker-compose.prod.yml up -d

# 僅重啟應用服務（不重啟資料庫）
docker compose restart backend nginx

# === 強制重建容器 ===
# 當容器狀態異常，restart 無效時使用
docker compose up -d --force-recreate backend

# === 查看服務狀態 ===
docker compose ps
docker compose logs --tail=50 backend
docker compose logs --tail=50 -f backend  # 持續追蹤日誌
```

### 9.4 水平擴展

**場景：** 流量增加，需要擴展後端 Worker 數量

```bash
# === 方法 1: Docker Compose scale（推薦） ===

# 擴展 backend 至 3 個 replica
docker compose -f docker-compose.prod.yml up -d --scale backend=3

# 確認擴展結果
docker compose ps

# 縮減回 2 個 replica
docker compose -f docker-compose.prod.yml up -d --scale backend=2

# === 方法 2: 調整 Uvicorn workers ===
# 修改 docker-compose.prod.yml 中的 command
# command: uvicorn smart_lock.main:app --host 0.0.0.0 --port 8000 --workers 4

# === 方法 3: 調整 PostgreSQL 連線池 ===
# 修改 .env 中的連線池設定
# DATABASE_POOL_SIZE=30        # 預設 20
# DATABASE_MAX_OVERFLOW=15     # 預設 10
```

**擴展注意事項：**
- V1.0 目標並發數：>= 50 users。Docker Compose + 2 workers 足夠
- V2.0 目標並發數：>= 100 users。可擴展至 3-4 workers
- 擴展 backend 後，確認 PostgreSQL 連線池大小足夠（每個 worker 佔用 pool_size 個連線）
- Redis 為單線程，通常不需要水平擴展，但需監控記憶體使用率

### 9.5 日誌查詢

**場景：** 排查問題時需要查詢日誌

```bash
# === 查看即時日誌 ===

# 追蹤所有服務日誌
docker compose logs -f

# 追蹤特定服務日誌
docker compose logs -f backend

# 查看最近 100 行日誌
docker compose logs --tail=100 backend

# === 搜尋特定內容 ===

# 搜尋錯誤日誌
docker compose logs backend 2>&1 | grep -i "error"

# 搜尋特定 request_id
docker compose logs backend 2>&1 | grep "req_abc123"

# 搜尋特定用戶的對話記錄
docker compose logs backend 2>&1 | grep "U1234567890"

# 搜尋 LLM 呼叫相關日誌
docker compose logs backend 2>&1 | grep "llm_call\|llm_token\|resolution_level"

# === 日誌匯出 ===

# 匯出特定時間範圍的日誌
docker compose logs --since="2026-02-25T00:00:00" --until="2026-02-25T23:59:59" backend > /tmp/backend-logs-20260225.txt

# === PostgreSQL 慢查詢日誌 ===
docker compose exec db psql -U smartlock -d smart_lock -c "SELECT * FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;"
```

### 9.6 SSL 憑證更新

**場景：** Let's Encrypt 憑證到期前更新

```bash
#!/bin/bash
# scripts/renew-ssl.sh

set -e

DEPLOY_DIR="/opt/smartlock"
DOMAIN="your-domain.com"

echo "=== 更新 SSL 憑證 ==="

# Step 1: 使用 certbot 更新憑證
certbot renew --quiet

# Step 2: 複製新憑證至 Nginx 目錄
cp /etc/letsencrypt/live/${DOMAIN}/fullchain.pem ${DEPLOY_DIR}/certs/
cp /etc/letsencrypt/live/${DOMAIN}/privkey.pem ${DEPLOY_DIR}/certs/

# Step 3: 重新載入 Nginx
docker compose exec nginx nginx -s reload

echo "SSL 憑證更新完成"
```

**建議設定自動更新 CronJob：**

```bash
# 每月 1 日凌晨 2 點自動更新 SSL 憑證
0 2 1 * * /opt/smartlock/scripts/renew-ssl.sh >> /opt/smartlock/logs/ssl-renew.log 2>&1
```

### 9.7 密鑰輪替

**場景：** 定期輪替 API Key 與密碼

```bash
# === JWT Secret 輪替 ===

# Step 1: 生成新的 JWT Secret
NEW_SECRET=$(openssl rand -hex 32)

# Step 2: 更新 .env 檔案
# 編輯 .env 中的 JWT_SECRET_KEY

# Step 3: 重啟後端服務（已發行的 Token 將失效）
docker compose restart backend

# === 資料庫密碼輪替 ===

# Step 1: 更新 PostgreSQL 密碼
docker compose exec db psql -U smartlock -c "ALTER USER smartlock WITH PASSWORD 'new_password';"

# Step 2: 更新 .env 中的 DATABASE_URL 和 POSTGRES_PASSWORD

# Step 3: 重啟後端服務
docker compose restart backend

# === Google API Key 輪替 ===

# Step 1: 在 Google Cloud Console 建立新的 API Key
# Step 2: 更新 .env 中的 GOOGLE_API_KEY
# Step 3: 重啟後端服務
docker compose restart backend
# Step 4: 確認服務正常後，在 Google Cloud Console 撤銷舊 Key
```

### 9.8 災難復原

**場景：** 主機故障或資料損毀，需要從零恢復

```bash
#!/bin/bash
# scripts/disaster-recovery.sh
# 在新主機上執行完整恢復

set -e

echo "=== 災難復原流程 ==="

# Step 1: 安裝必要軟體
echo "--- Step 1: 安裝 Docker ---"
curl -fsSL https://get.docker.com | sh
apt-get install -y docker-compose-plugin certbot

# Step 2: 建立目錄結構
DEPLOY_DIR="/opt/smartlock"
mkdir -p ${DEPLOY_DIR}/{nginx/conf.d,certs,backups,uploads,logs,scripts}

# Step 3: 從備份儲存中取回設定檔與最新備份
echo "--- Step 3: 取回設定檔與備份 ---"
# 從安全儲存複製 docker-compose.prod.yml, .env, nginx/ 等設定
# 從異地備份複製最新的資料庫備份檔案
# (具體指令視備份儲存方式而定)

# Step 4: 設定 SSL 憑證
echo "--- Step 4: 設定 SSL ---"
certbot certonly --standalone -d your-domain.com
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ${DEPLOY_DIR}/certs/
cp /etc/letsencrypt/live/your-domain.com/privkey.pem ${DEPLOY_DIR}/certs/

# Step 5: 啟動基礎服務
echo "--- Step 5: 啟動基礎服務 ---"
cd ${DEPLOY_DIR}
docker compose -f docker-compose.prod.yml up -d db redis

# Step 6: 等待 PostgreSQL 就緒
echo "--- Step 6: 等待 PostgreSQL 就緒 ---"
sleep 15
docker compose exec db pg_isready -U smartlock

# Step 7: 還原資料庫
echo "--- Step 7: 還原資料庫 ---"
LATEST_BACKUP=$(ls -t ${DEPLOY_DIR}/backups/*.sql.gz | head -1)
echo "使用備份: ${LATEST_BACKUP}"
gunzip -c ${LATEST_BACKUP} | docker compose exec -T db psql -U smartlock -d smart_lock

# Step 8: 執行 pending migrations
echo "--- Step 8: 執行 migrations ---"
docker compose run --rm api alembic upgrade head

# Step 9: 啟動全部服務
echo "--- Step 9: 啟動全部服務 ---"
docker compose -f docker-compose.prod.yml up -d

# Step 10: 驗證
echo "--- Step 10: 驗證 ---"
sleep 15
curl -f https://your-domain.com/health && echo "災難復原完成" || echo "驗證失敗，請手動排查"

# Step 11: 更新 DNS 記錄（如 IP 變更）
echo "如主機 IP 變更，請更新 DNS A Record 與 LINE Webhook URL"

# Step 12: 設定自動備份與監控
(crontab -l 2>/dev/null; echo "0 3 * * * cd ${DEPLOY_DIR} && ./scripts/backup.sh >> ${DEPLOY_DIR}/logs/backup.log 2>&1") | crontab -

echo "=== 災難復原流程結束 ==="
```

**RPO / RTO 目標：**

| 指標 | 目標 | 說明 |
| :--- | :--- | :--- |
| **RPO (Recovery Point Objective)** | <= 24 小時 | 每日凌晨 3 點備份，最多丟失 24 小時資料 |
| **RTO (Recovery Time Objective)** | <= 2 小時 | 從發現問題到服務恢復的最大時間 |

---

## 第 10 部分：環境專屬配置

### 10.1 Development 環境

**用途：** 本地功能開發、單元測試、除錯

```bash
# 啟動開發環境
docker compose up -d

# 啟動含前端的完整環境 (V2.0)
docker compose --profile v2 up -d

# 查看日誌
docker compose logs -f backend

# 停止環境
docker compose down
```

**開發環境特性：**
- Backend 啟用 `--reload` (Hot Reload)
- Frontend 啟用 `npm run dev` (HMR)
- Source code 透過 Volume 掛載至容器內
- PostgreSQL / Redis 端口對外暴露（方便本地工具連線）
- 使用 `.env` 的開發配置
- LINE Bot 使用 ngrok 建立暫時公開 URL
- FastAPI 自動產生的 `/docs` 可存取

**ngrok 設定（LINE Webhook 開發用）：**

```bash
# 安裝 ngrok
brew install ngrok  # macOS

# 啟動 ngrok tunnel
ngrok http 8000

# 取得公開 URL 後，至 LINE Developers Console 設定 Webhook URL
# https://xxxx.ngrok-free.app/webhook
```

### 10.2 Staging 環境

**用途：** 整合測試、UAT 驗收、部署前最後驗證

**與 Production 的差異：**

| 項目 | Staging | Production |
| :--- | :--- | :--- |
| LINE Channel | 獨立的 Staging Channel | 正式 Channel |
| Google AI | 開發帳號（低用量上限） | 正式帳號 |
| 資料 | 匿名化的生產資料副本 | 真實資料 |
| 備份 | 每週備份 | 每日備份（保留 30 天） |
| 日誌等級 | INFO | INFO |
| API 文件 | `/docs` 可存取 | `/docs` 關閉 |
| SSL | 自簽憑證或 Let's Encrypt | Let's Encrypt |
| Replicas | 1 | 2 |

### 10.3 Production 環境

**用途：** 正式對外服務環境

**生產環境特別注意事項：**
- 所有敏感端口不對外暴露
- FastAPI Debug 模式關閉（`APP_DEBUG=false`）
- `/docs` 與 `/openapi.json` 端點建議關閉或限制存取
- 所有容器設定 `restart: always`
- 容器資源設定上限（CPU, Memory）
- 結構化 JSON 日誌 + log rotation
- 每日自動備份，保留 30 天
- SSL/TLS 強制（HTTP 301 至 HTTPS）
- Rate Limiting 啟用
- 健康檢查啟用

### 10.4 環境變數完整清單

```bash
# =================================================================
# .env.example - 環境變數範本
# 複製此檔案為 .env 並填入實際值
# .env 不得提交至版本控制
# =================================================================

# === Application ===
APP_ENV=development                     # development / staging / production
APP_DEBUG=true                          # true (dev) / false (staging, prod)
APP_SECRET_KEY=your-secret-key-here

# === Database ===
DATABASE_URL=postgresql+asyncpg://user:password@db:5432/smart_lock
DATABASE_POOL_SIZE=20                   # dev: 5 / staging: 10 / prod: 20
DATABASE_MAX_OVERFLOW=10                # dev: 5 / staging: 5 / prod: 10

# === Redis ===
REDIS_URL=redis://redis:6379/0
SESSION_TTL_SECONDS=3600                # 對話 Session 超時：1 小時

# === LINE Messaging API ===
LINE_CHANNEL_SECRET=your-channel-secret
LINE_CHANNEL_ACCESS_TOKEN=your-access-token

# === Google AI ===
GOOGLE_API_KEY=your-api-key
GOOGLE_MODEL=gemini-3-pro
GOOGLE_EMBEDDING_MODEL=text-embedding-004

# === Auth ===
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60      # Admin: 60 (1h) / Technician: 480 (8h)
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# === AI Engine ===
CASE_LIBRARY_CONFIDENCE_THRESHOLD=0.85  # L1 向量搜尋相似度閾值
RAG_CONFIDENCE_THRESHOLD=0.70           # L2 RAG 信心度閾值
VECTOR_SEARCH_TOP_K=5                   # 向量搜尋回傳筆數

# === PostgreSQL (docker-compose) ===
POSTGRES_DB=smart_lock
POSTGRES_USER=smartlock
POSTGRES_PASSWORD=your-db-password

# === Google Maps API (V2.0) ===
GOOGLE_MAPS_API_KEY=your-maps-api-key

# === Logging ===
LOG_LEVEL=DEBUG                         # DEBUG (dev) / INFO (staging, prod)
LOG_FORMAT=json                         # json (all environments)

# === Container Registry (CI/CD) ===
REGISTRY=ghcr.io
IMAGE_PREFIX=your-org/smartlock
IMAGE_TAG=latest
```

**各環境變數差異速查表：**

| 變數 | Development | Staging | Production |
| :--- | :--- | :--- | :--- |
| `APP_ENV` | development | staging | production |
| `APP_DEBUG` | true | false | false |
| `DATABASE_POOL_SIZE` | 5 | 10 | 20 |
| `DATABASE_MAX_OVERFLOW` | 5 | 5 | 10 |
| `LOG_LEVEL` | DEBUG | INFO | INFO |
| `LINE_CHANNEL_*` | 開發 Channel | Staging Channel | 正式 Channel |
| `GOOGLE_API_KEY` | 開發帳號 (低上限) | 開發帳號 | 正式帳號 |

---

**重要提醒：** 所有部署程序在執行至生產環境前，務必先在 Staging 環境完成驗證。保持部署流程的自動化與可重複性，減少人為操作錯誤。定期演練災難復原流程，確保在真正需要時能夠順利執行。
