# 專案架構 — Services & Nginx Routing

## 整體架構

```
[Browser]
    ↓
[Nginx :80/:443]  10.10.172.127
    ├── /api/*        → Django :8000  (REST API)
    ├── /admin/*      → Django :8000  (Django Admin)
    ├── /static/*     → static files  (Django collectstatic)
    ├── /media/*      → media files
    └── /*            → React :3000   (SPA 前端)

[Django]  ai-django:8000
    ├── PostgreSQL  postgres_db:5432  (或 10.10.172.123:5432)
    ├── Redis       ai-redis:6379
    └── Dify API    http://10.253.43.244/v1/

[Celery Worker / Beat]  (ai-celery-worker, ai-celery-beat)
    └── Broker/Result → Redis :6379/1 & /2

[Dify]  10.10.172.37:80
    ├── Chat API    /v1/chat-messages
    ├── Dataset API /v1/datasets/
    └── Embedding / RAG
```

---

## 技術堆疊

| 層次 | 技術 | 版本/說明 |
|------|------|-----------|
| 前端 | React | Create React App，npm start |
| 後端框架 | Django | Python，`python manage.py runserver` |
| 背景任務 | Celery Worker + Beat | concurrency=2，DatabaseScheduler |
| 任務監控 | Celery Flower | port 5555 |
| 資料庫 | PostgreSQL + pgvector | pg15，ai_platform / ai_platform_dev |
| 快取/佇列 | Redis 7 | AOF 持久化 |
| AI 服務 | Dify | 外部主機 10.10.172.37 |
| 反向代理 | Nginx | HTTP/1.1，SSE 支援 |
| 容器管理 | Portainer | port 9000/9443 |
| 容器化 | Docker Compose | v2 |

---

## 目錄結構

```
ai-platform-web/
├── backend/              # Django 應用程式
│   ├── ai_platform/      # Django 專案設定 (settings.py)
│   ├── api/              # REST API views, models, serializers
│   │   └── views/
│   ├── library/          # 共用邏輯 (dify_integration, analytics...)
│   └── manage.py
├── frontend/             # React 應用程式
│   ├── src/
│   └── public/
├── config/               # ⭐ 主設定檔
│   ├── settings.yaml     # IP / 服務設定（修改 IP 從這裡改）
│   └── config_loader.py  # 讀取設定 + 環境變數覆寫
├── library/              # 後端共用函式庫（掛載進容器）
│   ├── config/
│   │   ├── dify_config.py
│   │   └── dify_config_manager.py
│   └── dify_integration/
├── nginx/
│   └── nginx.conf        # Nginx 反向代理設定
├── scripts/              # DB 初始化腳本
├── deployments/
│   └── database-server/  # 獨立 DB 主機的 docker-compose
├── docker-compose.yml    # 主要 Docker Compose
├── docker-compose.override.yml  # develop 環境覆寫
└── .github/
    └── skills/
        └── ai-platform-infra/  # 本 skill
```

---

## Nginx 路由規則摘要

| 路徑 | 代理目標 | 備註 |
|------|----------|------|
| `/api/*` | `ai-django:8000` | SSE 支援（proxy_buffering off） |
| `/admin/*` | `ai-django:8000` | Django Admin |
| `/static/*` | static volume | collectstatic 產出 |
| `/media/*` | media volume | 上傳檔案 |
| `/*` (fallback) | `ai-react:3000` | React SPA |

---

## 系統監控端點

Django 後端提供系統監控 API，監控閾值設定於 `config/settings.yaml`：

```yaml
system_monitoring:
  thresholds:
    cpu:    { warning: 80, critical: 90 }
    memory: { warning: 80, critical: 90 }
    disk:   { warning: 85, critical: 95 }
```

監控的 DB 資料表：users, know_issues, projects, rvt_guides, ocr_benchmarks, test_classes, employees, user_profiles

---

## 重要 API 路徑

| 功能 | 路徑 |
|------|------|
| Dify 知識庫 | `/api/dify/knowledge/retrieval/` |
| Protocol Chat | `/api/protocol-chat/` |
| 系統監控 | `/api/system-monitoring/` |
| 用戶管理 | `/admin/user-management` |
| Benchmark | `/api/benchmark/` |
