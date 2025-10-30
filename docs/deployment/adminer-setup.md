# Adminer 設定與使用指南

## 📋 概述

Adminer 是一個輕量級的資料庫管理工具，支援 PostgreSQL、MySQL、SQLite 等多種資料庫。本指南說明如何在 Docker 環境中設定和使用 Adminer 來管理 PostgreSQL 資料庫。

## 🛠️ 系統需求

- Docker & Docker Compose
- 運行中的 PostgreSQL 容器
- 網路瀏覽器

## ⚙️ Docker Compose 設定

### 基本配置

```yaml
services:
  postgres:
    image: postgres:15-alpine
    container_name: postgres_db
    restart: unless-stopped
    environment:
      POSTGRES_DB: ai_platform
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres123
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - /etc/localtime:/etc/localtime:ro
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - custom_network

  adminer:
    image: adminer:latest
    container_name: adminer_nas
    restart: unless-stopped
    ports:
      - "9090:8080"
    depends_on:
      - postgres
    networks:
      - custom_network

networks:
  custom_network:
    driver: bridge
```

### 重要設定說明

- **ports**: `9090:8080` - Adminer 網頁界面對應到主機的 9090 埠
- **networks**: 使用自定義網路確保容器間可以互相通訊
- **depends_on**: 確保 PostgreSQL 容器先啟動
- **restart**: `unless-stopped` 確保容器自動重啟

## 🚀 啟動服務

### 啟動 Adminer

```bash
# 啟動 Adminer 容器
docker compose up -d adminer

# 檢查容器狀態
docker compose ps

# 查看 Adminer 日誌
docker compose logs -f adminer
```

### 驗證服務運行

```bash
# 檢查所有相關容器
docker compose ps adminer postgres

# 測試網路連接
curl -I http://localhost:9090
```

## 🌐 存取 Adminer 網頁界面

### 登入資訊

- **網址**: http://localhost:9090
- **遠端存取**: http://10.10.172.127:9090 (從其他機器存取)

### 資料庫連線設定

在 Adminer 登入頁面填入以下資訊：

| 欄位 | 值 | 說明 |
|------|-----|------|
| **資料庫系統** | PostgreSQL | 從下拉選單選擇 |
| **伺服器** | `postgres` | 容器服務名稱 |
| **使用者名稱** | `postgres` | 資料庫使用者 |
| **密碼** | `postgres123` | 資料庫密碼 |
| **資料庫** | `ai_platform` | 目標資料庫名稱 |

### 連線步驟

1. 開啟瀏覽器前往 http://localhost:9090
2. 確認「資料庫系統」選擇 **PostgreSQL**
3. 填入上述連線資訊
4. 點擊「登入」按鈕
5. 成功後會看到資料庫結構和管理界面

## 📊 使用 Adminer

### 基本操作

#### 1. 瀏覽資料表
- 左側導航：選擇資料庫 → 資料表結構 → 點擊資料表名稱
- 主畫面：顯示資料表內容和結構

#### 2. 執行 SQL 查詢
- 點擊「SQL 命令」
- 輸入 SQL 語句
- 點擊「執行」

#### 3. 管理資料表
- **建立資料表**: 點擊「建立資料表」
- **修改結構**: 點擊資料表名稱 → 「修改資料表結構」
- **匯入資料**: 點擊「匯入」
- **匯出資料**: 點擊「匯出」

### 常用 SQL 範例

#### 基本查詢
```sql
-- 列出所有資料表
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';

-- 查看資料表結構
\d users

-- 查詢資料
SELECT * FROM users;
SELECT * FROM users WHERE name LIKE '%Alice%';
```

#### 資料操作
```sql
-- 新增資料
INSERT INTO users (name, email) VALUES ('John Doe', 'john@example.com');

-- 更新資料
UPDATE users SET email = 'newemail@example.com' WHERE id = 1;

-- 刪除資料
DELETE FROM users WHERE id = 1;
```

#### 資料表管理
```sql
-- 建立資料表
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    price DECIMAL(10,2),
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 新增欄位
ALTER TABLE products ADD COLUMN description TEXT;

-- 建立索引
CREATE INDEX idx_products_category ON products(category);
```

## 🔧 進階設定

### 環境變數配置

可以在 `docker-compose.yml` 中為 Adminer 新增環境變數：

```yaml
adminer:
  image: adminer:latest
  container_name: adminer_nas
  restart: unless-stopped
  environment:
    ADMINER_DEFAULT_SERVER: postgres
    ADMINER_DESIGN: pepa-linha    # 更改主題
  ports:
    - "9090:8080"
  depends_on:
    - postgres
  networks:
    - custom_network
```

### 自定義插件

```yaml
adminer:
  image: adminer:latest
  volumes:
    - ./adminer-plugins:/var/www/html/plugins-enabled
```

## 🛡️ 安全性考量

### 基本安全措施

1. **限制網路存取**
```yaml
ports:
  - "127.0.0.1:9090:8080"  # 只允許本機存取
```

2. **使用強密碼**
- 變更 PostgreSQL 預設密碼
- 定期更新存取憑證

3. **防火牆設定**
```bash
# 只允許特定 IP 存取 9090 埠
sudo ufw allow from 192.168.1.0/24 to any port 9090
```

### 生產環境建議

- 使用 HTTPS (搭配 reverse proxy)
- 實施 IP 白名單
- 定期備份資料庫
- 監控存取日誌

## 📋 管理命令

### Docker Compose 指令

```bash
# 啟動服務
docker compose up -d adminer

# 停止服務
docker compose stop adminer

# 重啟服務
docker compose restart adminer

# 移除服務
docker compose down adminer

# 查看日誌
docker compose logs -f adminer

# 清理並重建
docker compose down adminer
docker compose pull adminer
docker compose up -d adminer
```

### 資料庫維護

```bash
# 進入 PostgreSQL 容器
docker exec -it postgres_db psql -U postgres -d ai_platform

# 備份資料庫
docker exec postgres_db pg_dump -U postgres ai_platform > backup.sql

# 還原資料庫
cat backup.sql | docker exec -i postgres_db psql -U postgres -d ai_platform
```

## 🔍 故障排除

### 常見問題

#### 1. 無法存取 Adminer 網頁
```bash
# 檢查容器狀態
docker compose ps adminer

# 檢查埠號占用
ss -tlnp | grep 9090

# 檢查防火牆
sudo ufw status
```

#### 2. 無法連接到 PostgreSQL
```bash
# 檢查 PostgreSQL 容器
docker compose ps postgres

# 測試資料庫連線
docker exec postgres_db psql -U postgres -c '\l'

# 檢查網路連接
docker network ls
docker network inspect ai-platform-web_custom_network
```

#### 3. 權限問題
```bash
# 檢查資料庫權限
docker exec postgres_db psql -U postgres -c '\du'

# 重設密碼
docker exec postgres_db psql -U postgres -c "ALTER USER postgres PASSWORD 'newpassword';"
```

### 日誌分析

```bash
# 查看 Adminer 錯誤日誌
docker compose logs adminer | grep -i error

# 查看 PostgreSQL 日誌
docker compose logs postgres | grep -i error

# 即時監控日誌
docker compose logs -f adminer postgres
```

## 📈 效能最佳化

### Adminer 設定

- 限制同時連線數
- 設定查詢超時時間
- 使用連線池

### PostgreSQL 調校

```sql
-- 查看連線狀態
SELECT * FROM pg_stat_activity;

-- 監控查詢效能
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC LIMIT 10;
```

## 📚 相關資源

- [Adminer 官方文件](https://www.adminer.org/)
- [PostgreSQL 文件](https://www.postgresql.org/docs/)
- [Docker Compose 參考](https://docs.docker.com/compose/)

---

**建立日期**: 2025-09-08  
**維護者**: huangkk10  
**版本**: 1.0  
**狀態**: 運行中