# CSP Platform - AI 模型服務管理平台

內網 AI 模型服務管理平台，用於統一管理地端 AI 模型的 API Key 發行、使用量追蹤、權限控管，以及提供 OpenAI 相容的 API 代理層。

## 功能

- **API Key 管理**：發行、撤銷 API Key，支援模型權限控管
- **模型註冊**：支援 LLM、VLM、Embedding 模型，自動健康檢查
- **用量追蹤**：記錄每次 API 呼叫的 token 用量，支援折線圖分析
- **OpenAI 相容代理**：`/v1/chat/completions`、`/v1/embeddings`、`/v2/embeddings`
- **平台連結**：儀表板卡片連結到 n8n、GitLab、MyNotebookLM 等內網平台
- **使用者管理**：管理員/使用者角色權限
- **CSV 匯出**：匯出用量資料供報表使用
- **100% 離線**：無需外網連線

## Tech Stack

- **Backend**: Python 3.11 + FastAPI + SQLAlchemy + SQLite
- **Frontend**: Vue 3 + Vite + Tailwind CSS + Apache ECharts
- **Container**: Docker (multi-stage build)

## 快速開始

### Docker 部署（推薦）

```bash
cd docker
docker compose up -d
```

平台啟動後訪問 `http://localhost:8000`

- 預設管理員帳號：`admin`
- 預設密碼：`changeme`

### 模型自動註冊

編輯 `docker/docker-compose.yml` 中的 `AUTO_REGISTER_MODELS` 環境變數，CSP 平台啟動時會自動註冊你的模型：

```yaml
environment:
  - |
    AUTO_REGISTER_MODELS=[
      {
        "name": "llama3-70b",
        "display_name": "Llama 3 70B Instruct",
        "model_type": "llm",
        "endpoint_url": "http://vllm-llm:8000",
        "api_version": "v1"
      },
      {
        "name": "nv-embed-v2",
        "display_name": "NVIDIA NV-Embed V2",
        "model_type": "embedding",
        "endpoint_url": "http://triton-embedding:8000",
        "api_version": "v2"
      }
    ]
```

支援的 `model_type`：`llm`、`vlm`、`embedding`
支援的 `api_version`：`v1`（預設）、`v2`（用於 nv-embed-v2 的 `/v2/embeddings`）

同樣也可以自動註冊平台連結（儀表板卡片），設定 `AUTO_REGISTER_LINKS` 環境變數。

### 搭配模型服務一起部署

`docker/docker-compose.yml` 中已包含 vLLM、Triton、TensorRT-LLM 的範例設定（已註解），取消註解並修改路徑即可一起部署：

```bash
cd docker
# 編輯 docker-compose.yml，取消需要的模型服務註解
docker compose up -d
```

### 開發模式

```bash
# 1. 安裝後端依賴
cd backend
pip install -r requirements.txt

# 2. 初始化資料庫
cd ..
python scripts/init_db.py

# 3. 啟動後端
cd backend
uvicorn app.main:app --reload --port 8000

# 4. 安裝前端依賴並啟動（另一個終端）
cd frontend
npm install
npm run dev
```

## 使用 API 代理

註冊模型後，使用 API Key 呼叫模型：

```bash
# Chat Completions
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3-70b",
    "messages": [{"role": "user", "content": "你好"}]
  }'

# Embeddings (v1)
curl http://localhost:8000/v1/embeddings \
  -H "Authorization: Bearer sk-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "bge-m3",
    "input": "測試文字"
  }'

# Embeddings (v2, for nv-embed-v2)
curl http://localhost:8000/v2/embeddings \
  -H "Authorization: Bearer sk-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nv-embed-v2",
    "input": "測試文字"
  }'
```

## 環境變數

| 變數 | 預設值 | 說明 |
|------|-------|------|
| `SECRET_KEY` | - | JWT 加密金鑰（必須修改） |
| `DATABASE_URL` | `sqlite:///./data/csp.db` | 資料庫連線 |
| `ADMIN_USERNAME` | `admin` | 初始管理員帳號 |
| `ADMIN_PASSWORD` | `changeme` | 初始管理員密碼 |
| `EMBEDDING_TIMEOUT` | `30` | Embedding 請求逾時（秒） |
| `LLM_TIMEOUT` | `120` | LLM/VLM 請求逾時（秒） |
| `HEALTH_CHECK_INTERVAL` | `60` | 模型健康檢查間隔（秒） |

## 專案結構

```
myCSPPlatform/
├── backend/          # FastAPI 後端
│   ├── app/
│   │   ├── api/      # API 路由
│   │   ├── models/   # ORM 模型
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── services/ # 業務邏輯
│   │   └── utils/    # 工具函式
│   └── requirements.txt
├── frontend/         # Vue 3 前端
│   └── src/
│       ├── views/    # 頁面元件
│       ├── components/ # 共用元件
│       ├── stores/   # Pinia stores
│       └── api/      # API client
├── docker/           # Docker 設定
├── scripts/          # 初始化腳本
└── data/             # SQLite 資料庫
```
