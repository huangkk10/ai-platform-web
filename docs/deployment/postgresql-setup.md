# PostgreSQL 資料庫設定說明

## 服務概述
PostgreSQL 是一個功能強大的開源關聯式資料庫系統，具有強大的功能和可靠性。

## 資料庫連線資訊

### 連線參數
- **主機**: localhost
- **連接埠**: 5432
- **資料庫名稱**: ai_platform
- **使用者名稱**: postgres
- **密碼**: postgres123

### 連線字串範例
```bash
# psql 命令列連線
psql -h localhost -p 5432 -U postgres -d ai_platform

# 應用程式連線字串
postgresql://postgres:postgres123@localhost:5432/ai_platform
```

## 快速開始

### 啟動服務
```bash
# 啟動所有服務（包含 PostgreSQL）
docker compose up -d

# 只啟動 PostgreSQL
docker compose up -d postgres

# 檢查服務狀態
docker compose ps
```

### 連線到資料庫
```bash
# 使用 docker exec 連線
docker compose exec postgres psql -U postgres -d ai_platform

# 或者安裝 postgresql-client 後使用
sudo apt install postgresql-client
psql -h localhost -p 5432 -U postgres -d ai_platform
```

## 資料庫管理

### 常用 SQL 命令
```sql
-- 查看所有資料庫
\l

-- 切換資料庫
\c ai_platform

-- 查看所有資料表
\dt

-- 查看資料表結構
\d table_name

-- 建立新資料表範例
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入資料範例
INSERT INTO users (username, email) VALUES ('admin', 'admin@example.com');

-- 查詢資料
SELECT * FROM users;

-- 離開 psql
\q
```

### 備份與還原
```bash
# 備份資料庫
docker compose exec postgres pg_dump -U postgres ai_platform > backup.sql

# 還原資料庫
docker compose exec -T postgres psql -U postgres ai_platform < backup.sql

# 備份所有資料庫
docker compose exec postgres pg_dumpall -U postgres > all_backup.sql
```

## 設定詳解

### 環境變數說明
- `POSTGRES_DB`: 預設建立的資料庫名稱
- `POSTGRES_USER`: 超級使用者帳號
- `POSTGRES_PASSWORD`: 超級使用者密碼
- `PGDATA`: 資料目錄路徑

### Volume 掛載
- `postgres_data`: 持久化資料庫資料
- `/etc/localtime`: 同步系統時間

### 健康檢查
- 每 30 秒檢查資料庫是否可連線
- 超時時間 10 秒，重試 3 次

## 效能調優

### 記憶體設定
如需調整 PostgreSQL 記憶體設定，可以添加以下環境變數：
```yaml
environment:
  POSTGRES_SHARED_PRELOAD_LIBRARIES: pg_stat_statements
  POSTGRES_MAX_CONNECTIONS: 100
  POSTGRES_SHARED_BUFFERS: 256MB
  POSTGRES_EFFECTIVE_CACHE_SIZE: 1GB
```

### 自訂設定檔
```yaml
volumes:
  - ./postgresql.conf:/etc/postgresql/postgresql.conf
  - postgres_data:/var/lib/postgresql/data
command: postgres -c config_file=/etc/postgresql/postgresql.conf
```

## 安全設定

### 生產環境建議
1. **變更預設密碼**：
   ```sql
   ALTER USER postgres PASSWORD 'your_secure_password';
   ```

2. **建立應用程式專用使用者**：
   ```sql
   CREATE USER app_user WITH PASSWORD 'app_password';
   GRANT ALL PRIVILEGES ON DATABASE ai_platform TO app_user;
   ```

3. **限制網路存取**：
   ```yaml
   ports:
     - "127.0.0.1:5432:5432"  # 只允許本機存取
   ```

4. **使用環境變數檔案**：
   ```bash
   # 建立 .env 檔案
   echo "POSTGRES_PASSWORD=your_secure_password" > .env
   ```

## 監控與維護

### 查看資料庫狀態
```bash
# 查看服務日誌
docker compose logs postgres

# 查看即時日誌
docker compose logs -f postgres

# 檢查資料庫大小
docker compose exec postgres psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('ai_platform'));"
```

### 定期維護
```sql
-- 分析資料表統計資訊
ANALYZE;

-- 清理無用空間
VACUUM;

-- 重建索引
REINDEX DATABASE ai_platform;
```

## 故障排除

### 常見問題
1. **連線失敗**：
   - 檢查容器是否運行：`docker compose ps`
   - 檢查連接埠是否開放：`netstat -tlnp | grep 5432`

2. **密碼錯誤**：
   - 確認環境變數設定正確
   - 檢查是否有 .env 檔案覆蓋設定

3. **資料持久化問題**：
   - 確認 volume 正確掛載：`docker volume ls`
   - 檢查資料目錄權限

### 重設資料庫
```bash
# 停止服務
docker compose down

# 刪除資料 volume（⚠️ 會清除所有資料）
docker volume rm ai-platform-web_postgres_data

# 重新啟動
docker compose up -d postgres
```

## 工具推薦

### GUI 管理工具
- **pgAdmin**: Web 介面的 PostgreSQL 管理工具
- **DBeaver**: 跨平台資料庫管理工具
- **DataGrip**: JetBrains 的資料庫 IDE

### 命令列工具
- **psql**: PostgreSQL 官方命令列工具
- **pgcli**: 增強版的 psql，支援自動完成和語法高亮

---
**建立日期**: 2025-09-08  
**維護者**: huangkk10  
**版本**: PostgreSQL 15 Alpine