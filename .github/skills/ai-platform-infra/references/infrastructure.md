# Infrastructure — IP / Port / Service Reference

## 主機清單

| 主機名稱 | IP 位址 | 角色 |
|----------|---------|------|
| **AI PC (Dify)** | `10.253.43.244` | 運行 Dify，提供 LLM / RAG API，SSH user: `svd` |
| **Web Server**   | `10.10.172.127` | 本機，運行 Django + React + Nginx，SSH user: `user` |
| **Database Server** | `10.10.172.123` | 獨立 PostgreSQL 主機，SSH user: `svd-ai` |

---

## 服務 Port 對照表

| 容器名稱 | Port (Host:Container) | 說明 |
|----------|-----------------------|------|
| `ai-nginx` | `80:80`, `443:443` | Web 入口，反向代理 |
| `ai-django` | `8000:8000` | Django REST API |
| `ai-react` | `3000:3000` | React 前端 (dev mode) |
| `postgres_db` | `5432:5432` | PostgreSQL（本地 dev 用） |
| `adminer_nas` | `9090:8080` | DB 管理介面 → `http://10.10.172.123:9090` |
| `ai-redis` | `6379:6379` | Redis (Celery broker) |
| `ai-celery-worker` | — | Celery Worker |
| `ai-celery-beat` | — | Celery Beat 排程 |
| `ai-celery-flower` | `5555:5555` | Celery 任務監控 |
| `portainer` | `9000:9000`, `9443:9443` | Docker 容器管理 |

---

## 對外 URL

| 用途 | URL |
|------|-----|
| Web 主入口 | `http://10.10.172.127` |
| Django API | `http://10.10.172.127/api/` |
| Django Admin | `http://10.10.172.127/admin/` |
| React (直連) | `http://10.10.172.127:3000` |
| Dify API | `http://10.253.43.244/v1/` |
| Dify UI | `http://10.253.43.244` |
| Dify Chat API | `http://10.253.43.244/v1/chat-messages` |
| Adminer (DB) | `http://10.10.172.123:9090` |
| Celery Flower | `http://10.10.172.127:5555` |
| Portainer | `http://10.10.172.127:9000` |

---

## 資料庫連線設定

生產/獨立主機（`config/settings.yaml`）:
```yaml
database_server:
  host: "10.10.172.123"
  port: 5432
  database: "ai_platform"
  user: "postgres"
  password: "postgres123"
```

本地 Docker 開發環境（`docker-compose.yml`）:
```yaml
DB_HOST: postgres_db
DB_PORT: 5432
DB_NAME: ai_platform_dev
DB_USER: postgres
DB_PASSWORD: postgres123
```

---

## Dify 設定

### AI PC IP
- 預設值：`10.253.43.244`
- 環境變數覆寫：`AI_PC_IP`
- 設定檔位置：`config/settings.yaml` → `ai_server.ai_pc_ip`

### Dify API Keys（依環境）

**開發環境** (dev App，連到 `10.10.172.127` 外部知識庫 API)：

| App | API Key |
|-----|---------|
| Protocol Known Issue (dev) | `app-X6qZZooKjG4WGk6l9hRSq2Y9` |
| Protocol Guide (dev) | `app-4TbH1O7NkpOFsnxGEF3FLyqd` |
| RVT Guide (dev) | `app-xDXNUVPnPkP1We12RonI6Jk6` |
| Report Analyzer 3 (dev) | `app-YgLRoc5LVuJyw8aY3KtxjXUg` |

**生產環境** (正式 App，連到 `10.10.172.123` 外部知識庫 API)：

| App | API Key |
|-----|---------|
| Protocol Known Issue | `app-Sql11xracJ71PtZThNJ4ZQQW` |
| Protocol Guide | `app-MgZZOhADkEmdUrj2DtQLJ23G` |
| RVT Guide | `app-Lp4mlfIWHqMWPHTlzF9ywT4F` |
| Report Analyzer 3 | `app-DmCCl8KwXhhjND0WbEf0ULlR` |

---

## Redis 設定

| 用途 | URL |
|------|-----|
| Django Cache | `redis://redis:6379/0` |
| Celery Broker | `redis://redis:6379/1` |
| Celery Result | `redis://redis:6379/2` |

---

## 環境變數設定檔位置

| 檔案 | 說明 |
|------|------|
| `config/settings.yaml` | **主設定檔**，AI PC IP、Web IP、DB Host |
| `docker-compose.yml` | Docker 服務環境變數（dev 容器內） |
| `docker-compose.override.yml` | develop branch 專用覆寫（Beta badge） |
| `backend/.env.example` | Django `.env` 範本 |
| `.env.example` | 根目錄 `.env` 範本 |
| `deployments/database-server/.env.example` | 獨立 DB 主機設定範本 |
