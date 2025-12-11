# 🐘 PostgreSQL 資料庫遷移計畫

## 📋 概述

**目標**：將現有的 PostgreSQL 資料庫容器從主機 `10.10.172.127` 遷移至新主機 `10.10.173.29`

### 環境資訊

| 項目 | 原主機 | 新主機 |
|------|--------|--------|
| IP | 10.10.172.127 | 10.10.173.29 |
| 用戶 | user | svd-ai |
| 密碼 | 1234 | 1 |
| PostgreSQL 版本 | pgvector/pgvector:pg15 | pgvector/pgvector:pg15 |
| 資料庫名稱 | ai_platform | ai_platform |
| DB 用戶 | postgres | postgres |
| DB 密碼 | postgres123 | postgres123 |
| 容器名稱 | postgres_db | postgres_db |

---

## 📂 方案 A：在主專案中管理資料庫配置（採用）

### 目錄結構
```
ai-platform-web/
├── deployments/
│   └── database-server/           ### Step 3.2：更新 settings.yaml（文檔用途）
修改 `### Step 3.4：重啟應用服務
```bash
# 在原主機上執行
cd /home/user/codes/ai-platform-web

# 停止所有服務
docker compose down

# 重新啟動服務（不包含已註釋的 postgres 和 adminer）
docker compose up -d

# 或者只啟動特定服務
docker compose up -d django celery_worker celery_beat celery_flower react nginx redis portainer

# 檢查服務狀態
docker compose ps
```codes/ai-platform-web/config/settings.yaml`：

```yaml
# 資料庫配置
database:
  postgres_host: "10.10.173.29"  # ← 新主機 IP（遷移後）
  postgres_port: 5432
  postgres_db: "ai_platform"
  postgres_user: "postgres"
  postgres_password: "postgres123"
  
  # 備註：實際連線由 docker-compose.yml 的環境變數控制
  # 此配置僅供文檔和監控參考
```

### Step 3.3：修改配置摘要表

| 修改項目 | 檔案 | 原值 | 新值 |
|----------|------|------|------|
| Django DB_HOST | docker-compose.yml | `postgres_db` | `10.10.173.29` |
| Celery Worker DB_HOST | docker-compose.yml | `postgres_db` | `10.10.173.29` |
| Celery Beat DB_HOST | docker-compose.yml | `postgres_db` | `10.10.173.29` |
| Django depends_on | docker-compose.yml | `postgres, redis` | `redis` |
| Celery Worker depends_on | docker-compose.yml | `postgres, redis, django` | `redis, django` |
| Celery Beat depends_on | docker-compose.yml | `postgres, redis, django` | `redis, django` |
| postgres 服務 | docker-compose.yml | 啟用 | 註釋掉 |
| adminer 服務 | docker-compose.yml | 啟用 | 註釋掉 |
| settings.yaml | config/settings.yaml | `localhost` | `10.10.173.29` |

### Step 3.4：重啟應用服務    ├── docker-compose.yml     # 新主機的 Docker 配置
│       ├── scripts/
│       │   └── init-pgvector.sql  # 資料庫初始化腳本
│       ├── .env.example           # 環境變數範例
│       ├── README.md              # 使用說明
│       └── sync-to-remote.sh      # 同步腳本
├── docs/
│   └── deployment/
│       └── database-migration-plan.md  # 本文檔
└── docker-compose.yml             # 原主機配置（需修改）
```

### 維護流程

#### 日常維護（在本機修改配置後同步到新主機）
```bash
# 方法一：使用同步腳本（推薦）
cd /home/user/codes/ai-platform-web/deployments/database-server
./sync-to-remote.sh

# 方法二：手動 scp
scp -r /home/user/codes/ai-platform-web/deployments/database-server/* \
    svd-ai@10.10.173.29:~/postgres-db-server/
# 密碼: 1

# 方法三：在新主機上使用 git（如果已設定）
ssh svd-ai@10.10.173.29
cd ~/postgres-db-server
git pull origin main
```

#### 更新配置後重啟服務
```bash
# SSH 到新主機
ssh svd-ai@10.10.173.29

# 重啟資料庫服務
cd ~/postgres-db-server
docker compose down
docker compose up -d

# 檢查狀態
docker compose ps
docker logs postgres_db --tail 50
```

---

## 🔍 專案中使用資料庫的完整分析

### 需要修改的配置檔案清單

| 檔案 | 位置 | 修改內容 |
|------|------|----------|
| docker-compose.yml | `/home/user/codes/ai-platform-web/` | 修改 4 個服務的 DB_HOST |
| settings.yaml | `/home/user/codes/ai-platform-web/config/` | 更新 postgres_host（文檔用途） |

### 使用資料庫的服務（共 4 個）

#### 1. Django 主服務 (`ai-django`)
```yaml
# docker-compose.yml 第 80-84 行
environment:
  - DB_HOST=postgres_db      # ← 需改為 10.10.173.29
  - DB_PORT=5432
  - DB_NAME=ai_platform
  - DB_USER=postgres
  - DB_PASSWORD=postgres123
depends_on:
  - postgres                  # ← 需移除
```

#### 2. Celery Worker (`ai-celery-worker`)
```yaml
# docker-compose.yml 第 114-118 行
environment:
  - DB_HOST=postgres_db      # ← 需改為 10.10.173.29
  - DB_PORT=5432
  - DB_NAME=ai_platform
  - DB_USER=postgres
  - DB_PASSWORD=postgres123
depends_on:
  - postgres                  # ← 需移除
```

#### 3. Celery Beat (`ai-celery-beat`)
```yaml
# docker-compose.yml 第 147-151 行
environment:
  - DB_HOST=postgres_db      # ← 需改為 10.10.173.29
  - DB_PORT=5432
  - DB_NAME=ai_platform
  - DB_USER=postgres
  - DB_PASSWORD=postgres123
depends_on:
  - postgres                  # ← 需移除
```

#### 4. Adminer (`adminer_nas`)
```yaml
# docker-compose.yml 第 42-48 行
# 此服務將遷移到新主機，原主機不再需要
```

### Django Settings 資料庫配置

```python
# backend/ai_platform/settings.py 第 74-82 行
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME': config('DB_NAME', default='ai_platform'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres123'),
        'HOST': config('DB_HOST', default='postgres_db'),  # ← 由環境變數控制
        'PORT': config('DB_PORT', default='5432'),
    }
}
```

**說明**：Django 使用 `python-decouple` 從環境變數讀取配置，只需修改 `docker-compose.yml` 中的環境變數即可，不需修改 `settings.py`。

---

## 🏗️ 架構變更概述

### 遷移前架構
```
[10.10.172.127]
├── ai-django (Port 8000)
├── ai-react (Port 3000)
├── ai-nginx (Port 80)
├── ai-celery-worker
├── ai-celery-beat
├── ai-redis (Port 6379)
├── postgres_db (Port 5432) ← 要遷移的服務
└── adminer (Port 9090)
```

### 遷移後架構
```
[10.10.172.127] (Web 應用主機)          [10.10.173.29] (資料庫主機)
├── ai-django ────────────────────────→ postgres_db (Port 5432)
├── ai-react                            └── adminer (Port 9090)
├── ai-nginx
├── ai-celery-worker
├── ai-celery-beat
└── ai-redis
```

---

## 📝 Phase 1：新主機準備（約 30 分鐘）

### Step 1.1：連接新主機並安裝 Docker
```bash
# 連接新主機
ssh svd-ai@10.10.173.29
# 密碼: 1

# 檢查 Docker 是否已安裝
docker --version
docker compose version

# 如果未安裝，執行以下命令
sudo apt update
sudo apt install -y docker.io docker-compose-plugin

# 將用戶加入 docker 群組
sudo usermod -aG docker svd-ai
# 重新登入使生效
exit
ssh svd-ai@10.10.173.29
```

### Step 1.2：建立專案目錄
```bash
# 在新主機上建立目錄
mkdir -p ~/postgres-db-server/scripts
cd ~/postgres-db-server
```

### Step 1.3：建立 Docker Compose 配置
在新主機 `10.10.173.29` 上建立 `docker-compose.yml`：

```yaml
# ~/postgres-db-server/docker-compose.yml
services:
  postgres:
    image: pgvector/pgvector:pg15
    container_name: postgres_db
    restart: unless-stopped
    environment:
      POSTGRES_DB: ai_platform
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres123
      PGDATA: /var/lib/postgresql/data/pgdata
      TZ: Asia/Taipei
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - /etc/localtime:/etc/localtime:ro
      - ./scripts/init-pgvector.sql:/docker-entrypoint-initdb.d/init-pgvector.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - db_network

  adminer:
    image: adminer:latest
    container_name: adminer_db
    restart: unless-stopped
    ports:
      - "9090:8080"
    depends_on:
      - postgres
    networks:
      - db_network

volumes:
  postgres_data:
    driver: local

networks:
  db_network:
    driver: bridge
```

### Step 1.4：建立初始化 SQL 腳本
將 `scripts/init-pgvector.sql` 複製到新主機：

```sql
-- ~/postgres-db-server/scripts/init-pgvector.sql
-- 初始化 pgvector 擴展
CREATE EXTENSION IF NOT EXISTS vector;

-- 創建文檔向量嵌入表
CREATE TABLE IF NOT EXISTS document_embeddings (
    id SERIAL PRIMARY KEY,
    source_table VARCHAR(100) NOT NULL,
    source_id INTEGER NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    embedding vector(384),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_table, source_id)
);

-- 創建向量相似度搜索索引
CREATE INDEX IF NOT EXISTS document_embeddings_vector_idx 
ON document_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 創建複合索引用於查詢優化
CREATE INDEX IF NOT EXISTS document_embeddings_source_idx 
ON document_embeddings(source_table, source_id);

-- 添加更新時間觸發器
CREATE OR REPLACE FUNCTION update_embedding_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_document_embeddings_updated_at ON document_embeddings;
CREATE TRIGGER update_document_embeddings_updated_at
    BEFORE UPDATE ON document_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_embedding_updated_at();
```

---

## 📝 Phase 2：資料備份與遷移（約 20-60 分鐘，視資料量）

### Step 2.1：在原主機上備份資料庫
```bash
# 在原主機 10.10.172.127 上執行
cd /home/user/codes/ai-platform-web

# 創建備份目錄
mkdir -p backups/database

# 備份整個資料庫（包含所有 schema 和資料）
docker exec postgres_db pg_dump -U postgres -d ai_platform --verbose --format=custom --file=/tmp/ai_platform_backup.dump

# 將備份檔案複製出容器
docker cp postgres_db:/tmp/ai_platform_backup.dump ./backups/database/ai_platform_backup_$(date +%Y%m%d_%H%M%S).dump

# 也可以使用 SQL 格式備份（更易讀）
docker exec postgres_db pg_dump -U postgres -d ai_platform > ./backups/database/ai_platform_backup_$(date +%Y%m%d_%H%M%S).sql
```

### Step 2.2：將備份檔案傳輸到新主機
```bash
# 在原主機上執行
scp ./backups/database/ai_platform_backup_*.dump svd-ai@10.10.173.29:~/postgres-db-server/
scp ./backups/database/ai_platform_backup_*.sql svd-ai@10.10.173.29:~/postgres-db-server/
# 密碼: 1
```

### Step 2.3：在新主機上啟動資料庫容器
```bash
# 在新主機 10.10.173.29 上執行
cd ~/postgres-db-server

# 啟動容器
docker compose up -d

# 檢查容器狀態
docker compose ps

# 等待 PostgreSQL 完全啟動（約 10-20 秒）
sleep 20

# 檢查連接
docker exec postgres_db pg_isready -U postgres
```

### Step 2.4：還原資料庫
```bash
# 在新主機上執行

# 方法一：使用 custom format 還原（推薦）
docker cp ~/postgres-db-server/ai_platform_backup_*.dump postgres_db:/tmp/
docker exec postgres_db pg_restore -U postgres -d ai_platform --verbose /tmp/ai_platform_backup_*.dump

# 方法二：使用 SQL 格式還原
docker cp ~/postgres-db-server/ai_platform_backup_*.sql postgres_db:/tmp/backup.sql
docker exec postgres_db psql -U postgres -d ai_platform -f /tmp/backup.sql
```

### Step 2.5：驗證資料完整性
```bash
# 在新主機上執行

# 檢查資料表
docker exec postgres_db psql -U postgres -d ai_platform -c "\dt"

# 檢查資料數量
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT 
    'auth_user' as table_name, COUNT(*) as count FROM auth_user
UNION ALL SELECT 'rvt_guide', COUNT(*) FROM rvt_guide
UNION ALL SELECT 'know_issue', COUNT(*) FROM know_issue
UNION ALL SELECT 'protocol_guide', COUNT(*) FROM protocol_guide
UNION ALL SELECT 'document_embeddings', COUNT(*) FROM document_embeddings;
"

# 檢查 pgvector 擴展
docker exec postgres_db psql -U postgres -d ai_platform -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

---

## 📝 Phase 3：修改原主機配置（約 10 分鐘）

### Step 3.1：修改 docker-compose.yml（完整版）

在原主機 `10.10.172.127` 上修改 `/home/user/codes/ai-platform-web/docker-compose.yml`：

#### 3.1.1 註釋掉 postgres 服務（第 16-40 行）
```yaml
  # ========== 已遷移到 10.10.173.29 ==========
  # postgres:
  #   image: pgvector/pgvector:pg15
  #   container_name: postgres_db
  #   restart: unless-stopped
  #   environment:
  #     POSTGRES_DB: ai_platform
  #     POSTGRES_USER: postgres
  #     POSTGRES_PASSWORD: postgres123
  #     PGDATA: /var/lib/postgresql/data/pgdata
  #     TZ: Asia/Taipei
  #   volumes:
  #     - postgres_data:/var/lib/postgresql/data
  #     - /etc/localtime:/etc/localtime:ro
  #     - ./scripts/init-pgvector.sql:/docker-entrypoint-initdb.d/init-pgvector.sql
  #   ports:
  #     - "5432:5432"
  #   healthcheck:
  #     test: [ "CMD-SHELL", "pg_isready -U postgres" ]
  #     interval: 30s
  #     timeout: 10s
  #     retries: 3
  #   networks:
  #     - custom_network
  # ========== END ==========
```

#### 3.1.2 註釋掉 adminer 服務（第 42-50 行）
```yaml
  # ========== 已遷移到 10.10.173.29 ==========
  # adminer:
  #   image: adminer:latest
  #   container_name: adminer_nas
  #   restart: unless-stopped
  #   ports:
  #     - "9090:8080"
  #   depends_on:
  #     - postgres
  #   networks:
  #     - custom_network
  # ========== END ==========
```

#### 3.1.3 修改 django 服務（第 71-104 行）
```yaml
  django:
    build:
      context: ./backend
    container_name: ai-django
    restart: unless-stopped
    command: python manage.py runserver 0.0.0.0:8000
    environment:
      - TZ=Asia/Taipei
      - DEBUG=1
      - DB_HOST=10.10.173.29      # ← 修改：從 postgres_db 改為新主機 IP
      - DB_PORT=5432
      - DB_NAME=ai_platform
      - DB_USER=postgres
      - DB_PASSWORD=postgres123
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_DB=0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - ./library:/app/library
      - ./config:/app/config
      - ./logs:/app/logs
      - static_files:/app/static
      - media_files:/app/media
    depends_on:
      # - postgres                 # ← 移除：不再依賴本地 postgres
      - redis
    networks:
      - custom_network
```

#### 3.1.4 修改 celery_worker 服務（第 106-139 行）
```yaml
  celery_worker:
    build:
      context: ./backend
    container_name: ai-celery-worker
    restart: unless-stopped
    command: celery -A ai_platform worker --loglevel=info --concurrency=2
    environment:
      - TZ=Asia/Taipei
      - DEBUG=1
      - DB_HOST=10.10.173.29      # ← 修改：從 postgres_db 改為新主機 IP
      - DB_PORT=5432
      - DB_NAME=ai_platform
      - DB_USER=postgres
      - DB_PASSWORD=postgres123
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_DB=0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
    volumes:
      - ./backend:/app
      - ./library:/app/library
      - ./config:/app/config
      - ./logs:/app/logs
      - static_files:/app/static
      - media_files:/app/media
    depends_on:
      # - postgres                 # ← 移除：不再依賴本地 postgres
      - redis
      - django
    networks:
      - custom_network
```

#### 3.1.5 修改 celery_beat 服務（第 141-176 行）
```yaml
  celery_beat:
    build:
      context: ./backend
    container_name: ai-celery-beat
    restart: unless-stopped
    command: celery -A ai_platform beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    environment:
      - TZ=Asia/Taipei
      - DEBUG=1
      - DB_HOST=10.10.173.29      # ← 修改：從 postgres_db 改為新主機 IP
      - DB_PORT=5432
      - DB_NAME=ai_platform
      - DB_USER=postgres
      - DB_PASSWORD=postgres123
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_DB=0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/2
    volumes:
      - ./backend:/app
      - ./library:/app/library
      - ./config:/app/config
      - ./logs:/app/logs
      - static_files:/app/static
      - media_files:/app/media
      - celery_beat_data:/app/celerybeat-schedule
    depends_on:
      # - postgres                 # ← 移除：不再依賴本地 postgres
      - redis
      - django
    networks:
      - custom_network
```

#### 3.1.6 修改 volumes 部分（可選，保留作為備份）
```yaml
volumes:
  portainer_data:
    driver: local
  # postgres_data:              # ← 可選：遷移穩定後可註釋掉
  #   driver: local
  pgadmin_data:
    driver: local
  redis_data:
    driver: local
  celery_beat_data:
    driver: local
  static_files:
    driver: local
  media_files:
    driver: local
  node_modules:
    driver: local
```

### Step 3.2：更新 settings.yaml（文檔用途）
修改 `/home/user/codes/ai-platform-web/config/settings.yaml`：

```yaml
# 資料庫配置
database:
  postgres_host: "10.10.173.29"  # ← 新主機 IP
  postgres_port: 5432
  postgres_db: "ai_platform"
```

### Step 3.3：重啟應用服務
```bash
# 在原主機上執行
cd /home/user/codes/ai-platform-web

# 停止所有服務
docker compose down

# 重新啟動服務（排除已移除的資料庫）
docker compose up -d django celery_worker celery_beat celery_flower react nginx redis portainer
```

---

## 📝 Phase 4：測試與驗證（約 15 分鐘）

### Step 4.1：測試資料庫連線
```bash
# 在原主機上測試遠端連線
docker exec ai-django python manage.py shell -c "
from django.db import connection
cursor = connection.cursor()
cursor.execute('SELECT 1')
print('資料庫連線成功:', cursor.fetchone())
"
```

### Step 4.2：測試應用功能
```bash
# 檢查 Django API
curl http://10.10.172.127/api/

# 檢查前端
curl http://10.10.172.127

# 檢查向量搜尋（如果有）
docker exec ai-django python -c "
from api.services.embedding_service import get_embedding_service
service = get_embedding_service()
print('向量服務正常')
"
```

### Step 4.3：測試完整流程
1. ✅ 登入系統
2. ✅ 查詢 Know Issue
3. ✅ 測試 RVT Assistant
4. ✅ 測試 Protocol Assistant
5. ✅ 確認所有功能正常

---

## 📝 Phase 5：清理原主機（可選，建議等待 1-2 週穩定後再執行）

### Step 5.1：移除舊的資料庫容器和資料
```bash
# ⚠️ 警告：確保新資料庫已經穩定運行後再執行！

# 停止並移除舊的 postgres 容器（如果還在運行）
docker stop postgres_db
docker rm postgres_db

# 移除舊的資料 volume（謹慎！）
docker volume rm ai-platform-web_postgres_data

# 或者保留備份後再刪除
# docker run --rm -v ai-platform-web_postgres_data:/data -v $(pwd)/backups:/backup alpine tar cvf /backup/postgres_data_final_backup.tar /data
```

---

## 🔄 回滾計畫（如果遷移失敗）

### 快速回滾步驟
```bash
# 1. 在原主機上，還原 docker-compose.yml 到原始版本
git checkout -- docker-compose.yml
git checkout -- config/settings.yaml

# 2. 重新啟動所有服務
docker compose up -d

# 3. 從備份還原資料（如果需要）
docker exec postgres_db psql -U postgres -d ai_platform -f /path/to/backup.sql

# 4. 驗證系統功能
curl http://10.10.172.127/api/
```

---

## 📊 遷移時間估計

| 階段 | 預估時間 | 備註 |
|------|----------|------|
| Phase 1：新主機準備 | 30 分鐘 | 包含 Docker 安裝 |
| Phase 2：資料備份與遷移 | 20-60 分鐘 | 視資料量而定 |
| Phase 3：修改原主機配置 | 10 分鐘 | |
| Phase 4：測試與驗證 | 15 分鐘 | |
| 緩衝時間 | 15 分鐘 | |
| **總計** | **1.5 - 2 小時** | |

---

## ⚠️ 風險評估與防範

### 高風險項目
| 風險 | 影響 | 防範措施 |
|------|------|----------|
| 資料遺失 | 嚴重 | 多重備份（custom + SQL 格式） |
| 網路中斷 | 中等 | 測試網路連通性後再遷移 |
| 連線配置錯誤 | 中等 | 仔細驗證每個服務的 DB_HOST |
| pgvector 版本不相容 | 中等 | 確保兩端使用相同版本 |

### 注意事項
1. **選擇低流量時段**：建議在非工作時間進行遷移
2. **通知相關人員**：遷移前告知所有系統使用者
3. **保留備份至少 2 週**：確認穩定後再清理
4. **防火牆設定**：確保 5432 port 在新主機上對外開放

---

## 📁 關於是否需要新 Repository

### 建議：**不需要**建立新的 Repository（採用方案 A）

**原因**：
1. 資料庫服務配置相對簡單，只需要一個 `docker-compose.yml` 和初始化腳本
2. 與主專案關聯性高，文檔和腳本應該保持在同一專案中
3. 已在主專案中建立 `deployments/database-server/` 目錄存放相關配置

### ✅ 已建立的目錄結構
```
ai-platform-web/
├── deployments/
│   └── database-server/           # ✅ 已建立
│       ├── docker-compose.yml     # 新主機的 Docker 配置
│       ├── scripts/
│       │   └── init-pgvector.sql  # 資料庫初始化腳本（含 384 維和 1024 維向量表）
│       ├── .env.example           # 環境變數範例
│       ├── README.md              # 詳細使用說明
│       └── sync-to-remote.sh      # 同步腳本
├── docs/
│   └── deployment/
│       └── database-migration-plan.md  # 本文檔
└── docker-compose.yml             # 原主機配置
```

### 📤 配置同步方式

#### 方式一：使用同步腳本（推薦）
```bash
# 設定 SSH key（首次）
ssh-copy-id svd-ai@10.10.173.29
# 密碼: 1

# 之後同步無需輸入密碼
cd /home/user/codes/ai-platform-web/deployments/database-server
chmod +x sync-to-remote.sh
./sync-to-remote.sh
```

#### 方式二：手動 scp
```bash
# 同步整個目錄
scp -r /home/user/codes/ai-platform-web/deployments/database-server/* \
    svd-ai@10.10.173.29:~/postgres-db-server/
# 密碼: 1

# 只同步特定檔案
scp /home/user/codes/ai-platform-web/deployments/database-server/docker-compose.yml \
    svd-ai@10.10.173.29:~/postgres-db-server/
```

#### 方式三：在新主機上設定 Git（進階）
```bash
# 在新主機上設定 sparse-checkout
ssh svd-ai@10.10.173.29
cd ~
git clone --depth 1 --filter=blob:none --sparse \
  https://github.com/huangkk10/ai-platform-web.git postgres-db-server
cd postgres-db-server
git sparse-checkout set deployments/database-server

# 之後更新
git pull
```

### 🔧 配置更新後的操作

當修改 `deployments/database-server/` 內的配置後：

```bash
# 1. 同步配置到新主機
cd /home/user/codes/ai-platform-web/deployments/database-server
./sync-to-remote.sh

# 2. SSH 到新主機並重啟服務
ssh svd-ai@10.10.173.29
cd ~/postgres-db-server
docker compose down
docker compose up -d

# 3. 驗證服務狀態
docker compose ps
docker logs postgres_db --tail 20
```

---

## 🗑️ 關於移除原本的資料庫

### 建議流程

1. **遷移完成後**：保持原資料庫運行作為備份（至少 1-2 週）
2. **確認穩定後**：
   - 停止原 postgres 容器
   - 修改 docker-compose.yml 註釋掉 postgres 和 adminer 服務
   - 備份 volume 資料
3. **2-4 週後**：如果一切正常，可以移除 volume

### 安全移除指令
```bash
# Step 1: 最終備份
docker exec postgres_db pg_dump -U postgres -d ai_platform > final_backup_before_removal.sql

# Step 2: 停止並移除容器
docker compose stop postgres adminer
docker compose rm -f postgres adminer

# Step 3: 備份 volume 到檔案
docker run --rm -v ai-platform-web_postgres_data:/data -v $(pwd)/backups:/backup alpine tar cvf /backup/postgres_volume_final.tar /data

# Step 4: 移除 volume（確認備份完成後）
docker volume rm ai-platform-web_postgres_data

# Step 5: 從 docker-compose.yml 移除相關服務定義
```

---

## 📞 支援聯繫

如遷移過程中遇到問題，請檢查：
1. 日誌：`docker logs postgres_db`
2. 網路連通：`ping 10.10.173.29`
3. Port 開放：`nc -zv 10.10.173.29 5432`

---

**文檔版本**：v1.1  
**建立日期**：2025-12-11  
**最後更新**：2025-12-11  
**維護者**：AI Platform Team

---

## 📋 附錄：快速檢查清單

### 遷移前檢查
- [ ] 新主機 SSH 可連線：`ssh svd-ai@10.10.173.29`
- [ ] 新主機 Docker 已安裝：`docker --version`
- [ ] 網路連通性：`ping 10.10.173.29`
- [ ] 5432 端口可用：`nc -zv 10.10.173.29 5432`

### 遷移中檢查
- [ ] 資料庫備份完成（.dump 和 .sql 格式）
- [ ] 備份檔案已傳輸到新主機
- [ ] 新主機 postgres 容器已啟動
- [ ] 資料已還原並驗證

### 遷移後檢查
- [ ] docker-compose.yml 已修改（DB_HOST x 3 處）
- [ ] depends_on 已移除 postgres（3 處）
- [ ] postgres/adminer 服務已註釋
- [ ] 服務已重啟且運行正常
- [ ] Django API 可訪問：`curl http://10.10.172.127/api/`
- [ ] 前端可訪問：`http://10.10.172.127`
- [ ] Adminer 可訪問：`http://10.10.173.29:9090`

### 相關檔案位置
| 檔案 | 用途 |
|------|------|
| `config/settings.yaml` | **資料庫連線資訊集中管理**（IP 變更時修改此處） |
| `deployments/database-server/docker-compose.yml` | 新主機資料庫配置 |
| `deployments/database-server/README.md` | 新主機使用說明 |
| `deployments/database-server/sync-to-remote.sh` | 配置同步腳本 |
| `docker-compose.yml` | 原主機服務配置（需修改） |
| `docs/deployment/database-migration-plan.md` | 本遷移計畫 |

---

## 🔧 附錄 B：資料庫連線資訊集中管理

### 為什麼要集中管理？

當資料庫主機 IP 變更時，需要修改多個檔案。為了避免遺漏和混亂，所有連線資訊統一記錄在 `config/settings.yaml`。

### settings.yaml 中的資料庫配置

```yaml
# config/settings.yaml

# 資料庫服務器配置
# ⚠️ 重要：資料庫已遷移到獨立主機，修改此配置後需同步更新 docker-compose.yml
database_server:
  host: "10.10.173.29"          # 資料庫主機 IP
  port: 5432                     # PostgreSQL 端口
  database: "ai_platform"        # 資料庫名稱
  user: "postgres"               # 資料庫用戶
  password: "postgres123"        # 資料庫密碼
  
  # SSH 連線資訊（用於維護）
  ssh_user: "svd-ai"
  ssh_password: "1"              # ⚠️ 建議改用 SSH key
  
  # Adminer Web 管理介面
  adminer_port: 9090
  adminer_url: "http://10.10.173.29:9090"
```

### 當資料庫主機 IP 變更時的處理流程

假設資料庫主機 IP 從 `10.10.173.29` 變更為 `10.10.173.99`：

#### Step 1：更新 settings.yaml（集中配置）
```bash
# 編輯配置檔案
nano /home/user/codes/ai-platform-web/config/settings.yaml

# 修改以下欄位：
# database_server:
#   host: "10.10.173.99"          # ← 新 IP
#   adminer_url: "http://10.10.173.99:9090"
```

#### Step 2：更新 docker-compose.yml（Web 應用主機）
```bash
# 編輯 docker-compose.yml
nano /home/user/codes/ai-platform-web/docker-compose.yml

# 搜尋並替換 DB_HOST（共 3 處）
# 將 DB_HOST=10.10.173.29 改為 DB_HOST=10.10.173.99

# 快速替換指令：
sed -i 's/DB_HOST=10.10.173.29/DB_HOST=10.10.173.99/g' docker-compose.yml
```

#### Step 3：更新同步腳本（如有需要）
```bash
# 如果新主機 SSH 資訊有變更
nano /home/user/codes/ai-platform-web/deployments/database-server/sync-to-remote.sh

# 修改 REMOTE_HOST 變數
# REMOTE_HOST="10.10.173.99"
```

#### Step 4：重啟服務
```bash
cd /home/user/codes/ai-platform-web
docker compose down
docker compose up -d
```

#### Step 5：驗證連線
```bash
# 測試資料庫連線
docker exec ai-django python manage.py shell -c "
from django.db import connection
cursor = connection.cursor()
cursor.execute('SELECT 1')
print('資料庫連線成功:', cursor.fetchone())
"
```

### IP 變更檢查清單

當資料庫主機 IP 變更時，確認以下項目都已更新：

| 檔案 | 需修改的內容 | 數量 |
|------|-------------|------|
| `config/settings.yaml` | `database_server.host`, `adminer_url` | 2 處 |
| `docker-compose.yml` | `DB_HOST` 環境變數 | 3 處 |
| `deployments/database-server/sync-to-remote.sh` | `REMOTE_HOST` | 1 處 |
| `docs/deployment/database-migration-plan.md` | 文檔中的 IP 參考 | 視需要 |

### 快速 IP 變更腳本（可選）

如果經常需要變更 IP，可以使用以下腳本：

```bash
#!/bin/bash
# scripts/update-db-host.sh
# 用法：./scripts/update-db-host.sh <新IP>

NEW_IP=$1
OLD_IP=$(grep -oP 'host: "\K[0-9.]+' config/settings.yaml | head -1)

if [ -z "$NEW_IP" ]; then
    echo "用法: $0 <新IP>"
    exit 1
fi

echo "將資料庫主機從 $OLD_IP 更新為 $NEW_IP"

# 更新 settings.yaml
sed -i "s/$OLD_IP/$NEW_IP/g" config/settings.yaml

# 更新 docker-compose.yml
sed -i "s/DB_HOST=$OLD_IP/DB_HOST=$NEW_IP/g" docker-compose.yml

# 更新同步腳本
sed -i "s/REMOTE_HOST=\"$OLD_IP\"/REMOTE_HOST=\"$NEW_IP\"/g" deployments/database-server/sync-to-remote.sh

echo "✅ 更新完成！請執行以下命令重啟服務："
echo "   docker compose down && docker compose up -d"
```
