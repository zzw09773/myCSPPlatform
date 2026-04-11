# CSP Platform

**Cloud Service Platform** — 企業內部 AI 模型服務的統一管理平台。

CSP 為組織提供一個集中式介面，用於管理多種 AI 模型（LLM、Embedding、VLM、Agent）的存取權限、API Key 發放、用量追蹤與健康監控。所有模型服務透過 OpenAI 相容 API 對外提供，讓使用者無需修改現有工具即可串接。

---

## 功能總覽

- **API Key 管理** — 發放 `sk-` 前綴的 OpenAI 格式金鑰，支援啟用 / 停用、到期日設定、模型存取權限控制
- **模型註冊** — 支援 LLM、Embedding、VLM、Agent 四種模型類型，可透過環境變數自動註冊
- **OpenAI 相容代理** — `/v1/chat/completions`、`/v1/embeddings`、`/v2/embeddings` 端點，支援 SSE Streaming
- **用量追蹤** — Token 用量即時統計、時序圖表、依模型 / 使用者分組、CSV 匯出
- **健康監控** — 背景定期檢查模型端點可用性，自動更新狀態
- **使用者管理** — 管理員可建立 / 編輯 / 停用使用者、重設密碼
- **平台卡片** — 儀表板顯示可自訂的快捷連結（GitLab、n8n、MLSteam 等）
- **Agent 支援** — 串接 MLSteam 等平台部署的 Agent 模型，支援 base_model 關聯

---

## 技術架構

```
                    ┌──────────────┐
      使用者 ──────▶│    Nginx     │ :80 (反向代理 + Rate Limit)
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   FastAPI    │ :8000 (後端 + SPA)
                    │  (CSP Core)  │
                    └──┬───────┬───┘
                       │       │
              ┌────────▼──┐ ┌──▼──────────┐
              │ PostgreSQL │ │  模型服務    │
              │   :5432    │ │ vLLM/Triton │
              └────────────┘ │ MLSteam/... │
                             └─────────────┘
```

| 層級 | 技術 |
|------|------|
| 前端 | Vue 3 + Vite + Tailwind CSS + Apache ECharts |
| 後端 | Python 3.11 + FastAPI + SQLAlchemy ORM |
| 資料庫 | PostgreSQL 16 |
| 反向代理 | Nginx (Alpine) |
| 容器化 | Docker + Docker Compose |
| 認證 | JWT (Access Token 15min + Refresh Token 7d) |

---

## 快速開始

### 前置需求

- Docker 及 Docker Compose v2+
- Git

### 步驟

```bash
# 1. 取得程式碼
git clone <repo-url> && cd myCSPPlatform

# 2. 建立環境變數檔
cp .env.example .env

# 3. 編輯配置（至少修改 SECRET_KEY 和 ADMIN_PASSWORD）
vim .env

# 4. 啟動平台
./start.sh up
```

啟動後存取：

| 服務 | 網址 |
|------|------|
| 管理平台 | http://localhost |
| API 文件 (Swagger) | http://localhost/docs |
| 健康檢查 | http://localhost/health |

預設管理員帳號：`admin` / `changeme`（請於 `.env` 修改）

---

## 配置說明

所有配置透過 `.env` 檔案管理。以下為各區塊說明：

### 基本設定

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `SECRET_KEY` | `your-secret-key-...` | JWT 簽署密鑰，**務必修改** |
| `DEBUG` | `false` | 除錯模式（啟用 SQL echo） |

### 資料庫

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `DATABASE_URL` | `postgresql://csp:csp_password@postgres:5432/csp` | PostgreSQL 連線字串 |
| `DB_USER` | `csp` | PostgreSQL 使用者（docker-compose 使用） |
| `DB_PASSWORD` | `csp_password` | PostgreSQL 密碼，**務必修改** |
| `DB_NAME` | `csp` | 資料庫名稱 |

### JWT 認證

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access Token 有效時間（分鐘） |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh Token 有效時間（天） |

### 管理員帳號

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `ADMIN_USERNAME` | `admin` | 首次啟動自動建立的管理員帳號 |
| `ADMIN_PASSWORD` | `changeme` | 管理員初始密碼，**務必修改** |

### Proxy 設定

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `EMBEDDING_TIMEOUT` | `30` | Embedding 請求逾時（秒） |
| `LLM_TIMEOUT` | `120` | LLM 請求逾時（秒） |
| `PROXY_MAX_RETRIES` | `3` | 代理失敗重試次數 |
| `PROXY_RETRY_BASE_DELAY` | `0.5` | 重試基礎延遲（秒，指數退避） |

### 背景任務

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `HEALTH_CHECK_INTERVAL` | `60` | 健康檢查間隔（秒） |
| `USAGE_BATCH_SIZE` | `100` | 用量批次寫入筆數 |
| `USAGE_FLUSH_INTERVAL` | `5` | 用量批次寫入間隔（秒） |

### Nginx

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `NGINX_PORT` | `80` | Nginx 對外 port |
| `SITE_URL` | `http://localhost` | 瀏覽器存取的基底 URL，用於平台卡片連結 |

---

## 模型註冊

模型可在啟動時透過環境變數自動註冊。支援兩種方式，可並存使用。

### 方式一：JSON 陣列

適合一次配置多個模型。在 `.env` 中設定 `AUTO_REGISTER_MODELS`：

```env
AUTO_REGISTER_MODELS=[
  {
    "name": "llama3-70b",
    "display_name": "Llama 3 70B Instruct",
    "model_type": "llm",
    "endpoint_url": "http://vllm-llm:8000",
    "api_version": "v1",
    "description": "vLLM 部署的 Llama 3 70B",
    "context_window": 8192
  },
  {
    "name": "nv-embed-v2",
    "display_name": "NVIDIA NV-Embed V2",
    "model_type": "embedding",
    "endpoint_url": "http://triton-embedding:8000",
    "api_version": "v2"
  },
  {
    "name": "aia/asrd",
    "display_name": "AIA ASRD Agent",
    "model_type": "agent",
    "endpoint_url": "http://mlsteam-host:45023",
    "api_version": "v1",
    "base_model": "llama3-70b"
  }
]
```

**模型類型 (`model_type`)：** `llm`、`embedding`、`vlm`、`agent`

**Agent 模型：** 透過 `base_model` 欄位指定底層模型的 `name`，系統會自動建立關聯。

### 方式二：獨立環境變數

適合逐一配置，格式為 `MODEL_<NAME>_<FIELD>`。`NAME` 使用底線分隔，系統自動轉為小寫連字號（如 `LLAMA3_70B` → `llama3-70b`）。

```env
MODEL_LLAMA3_70B_HOST=vllm-llm
MODEL_LLAMA3_70B_PORT=8000
MODEL_LLAMA3_70B_TYPE=llm
MODEL_LLAMA3_70B_DISPLAY_NAME=Llama 3 70B Instruct
MODEL_LLAMA3_70B_CONTEXT_WINDOW=8192

MODEL_NV_EMBED_V2_HOST=triton-embedding
MODEL_NV_EMBED_V2_PORT=8000
MODEL_NV_EMBED_V2_TYPE=embedding
MODEL_NV_EMBED_V2_API_VERSION=v2
```

**可用 FIELD：** `HOST`、`PORT`、`TYPE`、`DISPLAY_NAME`、`API_VERSION`、`DESCRIPTION`、`CONTEXT_WINDOW`、`BASE_MODEL`

> 兩種方式可並存。若 JSON 中已有相同 `name` 的模型，env var 不會覆蓋。

### 平台卡片連結

在 `.env` 中設定 `AUTO_REGISTER_LINKS`：

```env
AUTO_REGISTER_LINKS=[
  {"name": "n8n 工作流程", "url": "http://n8n:5678", "icon": "workflow", "description": "自動化工作流程平台"},
  {"name": "MLSteam", "url": "https://mlsteam.example.com", "icon": "cpu", "description": "MLOps 平台"}
]
```

---

## API 端點一覽

### 認證 (`/api/auth`)

| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/api/auth/login` | 登入，取得 access + refresh token |
| POST | `/api/auth/refresh` | 使用 refresh token 換發新 token |
| GET | `/api/auth/me` | 取得當前使用者資訊 |
| PUT | `/api/auth/password` | 修改自身密碼 |

### 使用者管理 (`/api/users`) — 需 Admin 權限

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/users` | 列出所有使用者 |
| POST | `/api/users` | 建立使用者 |
| GET | `/api/users/{id}` | 取得使用者詳情 |
| PUT | `/api/users/{id}` | 更新使用者資訊 |
| POST | `/api/users/{id}/reset-password` | 重設使用者密碼 |
| DELETE | `/api/users/{id}` | 停用使用者 |

### API Key 管理 (`/api/keys`)

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/keys` | 列出 API Keys |
| POST | `/api/keys` | 建立新 API Key（回傳 `sk-` 格式金鑰） |
| GET | `/api/keys/{id}` | 取得 Key 詳情 |
| PUT | `/api/keys/{id}` | 更新 Key 設定 |
| DELETE | `/api/keys/{id}` | 停用 Key |

### 模型管理 (`/api/models`)

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/models` | 列出所有已註冊模型 |
| POST | `/api/models` | 註冊新模型 |
| GET | `/api/models/{id}` | 取得模型詳情 |
| PUT | `/api/models/{id}` | 更新模型設定 |
| DELETE | `/api/models/{id}` | 移除模型 |
| POST | `/api/models/{id}/health-check` | 手動觸發健康檢查 |

### 用量統計 (`/api/usage`)

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/usage/summary` | 過去 24 小時用量摘要 |
| GET | `/api/usage/chart` | 時序圖表資料（支援 group_by） |
| GET | `/api/usage/top-models` | Top N 模型排行（30 天） |
| GET | `/api/usage/top-users` | Top N 使用者排行（30 天） |
| GET | `/api/usage/export` | 匯出用量 CSV |

### 平台連結 (`/api/platform-links`)

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/api/platform-links` | 列出所有平台卡片 |
| POST | `/api/platform-links` | 新增平台卡片 |
| PUT | `/api/platform-links/{id}` | 更新卡片 |
| DELETE | `/api/platform-links/{id}` | 刪除卡片 |

### OpenAI 相容代理

| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/v1/chat/completions` | Chat Completions（LLM / VLM / Agent） |
| POST | `/v1/embeddings` | Embeddings (v1 格式) |
| POST | `/v2/embeddings` | Embeddings (v2 格式，Triton 等) |

**代理使用方式：** 使用 API Key (`sk-...`) 作為 Bearer Token，將 CSP 當作 OpenAI endpoint 呼叫。

```bash
curl http://localhost/v1/chat/completions \
  -H "Authorization: Bearer sk-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3-70b",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": true
  }'
```

### 其他

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/health` | 健康檢查（容器編排用） |
| GET | `/docs` | Swagger UI API 文件 |

---

## 管理腳本

專案提供 `start.sh` 管理腳本，簡化 Docker Compose 操作：

```bash
./start.sh up        # 啟動所有服務（含建構映像）
./start.sh down      # 停止所有服務
./start.sh restart   # 重啟所有服務
./start.sh logs      # 查看所有日誌（Ctrl+C 退出）
./start.sh logs csp  # 只看 CSP 後端日誌
./start.sh status    # 查看容器狀態
./start.sh build     # 重新建構映像（不啟動）
./start.sh shell     # 進入後端容器 shell
```

---

## 專案結構

```
myCSPPlatform/
├── backend/
│   ├── app/
│   │   ├── api/          # API 路由（auth, users, keys, models, usage, proxy, links）
│   │   ├── models/       # SQLAlchemy ORM 模型
│   │   ├── schemas/      # Pydantic 請求/回應 schema
│   │   ├── services/     # 業務邏輯（auth, health_checker, usage_writer, auto_seed）
│   │   ├── utils/        # 工具函式（security, time_helpers）
│   │   ├── static/       # Swagger UI 靜態檔案
│   │   ├── config.py     # 設定（讀取 .env）
│   │   ├── database.py   # SQLAlchemy 引擎 & Session
│   │   └── main.py       # FastAPI 應用程式入口
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/        # 頁面元件（Dashboard, Models, Keys, Usage, Users）
│   │   ├── api/          # Axios client
│   │   └── router/       # Vue Router
│   ├── package.json
│   └── vite.config.js
├── docker/
│   ├── Dockerfile        # 多階段建構（Node + Python）
│   ├── docker-compose.yml
│   └── nginx.conf        # Nginx 反向代理配置
├── scripts/              # 輔助腳本
├── start.sh              # 管理腳本
├── .env.example          # 環境變數範本
└── README.md
```

---

## HTTPS 啟用

1. 將憑證放入 `docker/certs/` 目錄（`server.crt` + `server.key`）
2. 編輯 `docker/docker-compose.yml`，取消 SSL port 和 certs volume 的註解
3. 編輯 `docker/nginx.conf`，取消 HTTPS server block 的註解
4. 重啟服務：`./start.sh restart`

---

## 授權

內部使用專案。
