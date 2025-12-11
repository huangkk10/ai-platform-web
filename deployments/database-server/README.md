# 🐘 PostgreSQL Database Server

## 📋 概述

此目錄包含 AI Platform 專用的 PostgreSQL 資料庫服務器配置。

**部署位置**：`10.10.173.29`  
**服務端口**：
- PostgreSQL: `5432`
- Adminer (資料庫管理): `9090`

## 🚀 快速部署

### 首次部署

```bash
# 1. 在新主機上建立目錄
ssh svd-ai@10.10.173.29
mkdir -p ~/postgres-db-server
cd ~/postgres-db-server

# 2. 從主專案複製配置文件
# 方法 A：使用 scp
scp -r user@10.10.172.127:/home/user/codes/ai-platform-web/deployments/database-server/* .

# 方法 B：使用 git sparse-checkout
git clone --depth 1 --filter=blob:none --sparse \
  https://github.com/huangkk10/ai-platform-web.git .
git sparse-checkout set deployments/database-server
mv deployments/database-server/* .
rm -rf deployments .git

# 3. 設定環境變數（可選）
cp .env.example .env
nano .env

# 4. 啟動服務
docker compose up -d

# 5. 檢查狀態
docker compose ps
docker logs postgres_db
```

### 還原資料（從備份）

```bash
# 將備份檔案複製到容器
docker cp ai_platform_backup.dump postgres_db:/tmp/

# 還原資料
docker exec postgres_db pg_restore -U postgres -d ai_platform --verbose /tmp/ai_platform_backup.dump
```

## 🔄 更新配置

當主專案的配置更新後，同步到此服務器：

```bash
# 方法 A：使用 scp
cd ~/postgres-db-server
scp user@10.10.172.127:/home/user/codes/ai-platform-web/deployments/database-server/docker-compose.yml .
scp -r user@10.10.172.127:/home/user/codes/ai-platform-web/deployments/database-server/scripts/* ./scripts/

# 方法 B：如果使用 git
cd ~/postgres-db-server
git pull

# 重新啟動服務（如果配置有變更）
docker compose up -d
```

## 📊 常用指令

### 服務管理
```bash
# 啟動服務
docker compose up -d

# 停止服務
docker compose down

# 重啟服務
docker compose restart

# 查看日誌
docker compose logs -f postgres
docker compose logs -f adminer
```

### 資料庫操作
```bash
# 進入 PostgreSQL 命令行
docker exec -it postgres_db psql -U postgres -d ai_platform

# 執行 SQL 查詢
docker exec postgres_db psql -U postgres -d ai_platform -c "SELECT COUNT(*) FROM auth_user;"

# 查看所有資料表
docker exec postgres_db psql -U postgres -d ai_platform -c "\dt"

# 查看 pgvector 擴展狀態
docker exec postgres_db psql -U postgres -d ai_platform -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

### 備份與還原
```bash
# 備份資料庫
docker exec postgres_db pg_dump -U postgres -d ai_platform > backup_$(date +%Y%m%d).sql

# 使用 custom format 備份（推薦，較小且可選擇性還原）
docker exec postgres_db pg_dump -U postgres -d ai_platform -Fc > backup_$(date +%Y%m%d).dump

# 還原資料庫
docker exec -i postgres_db psql -U postgres -d ai_platform < backup.sql
```

## 🔗 連線資訊

### 從 Web 應用主機連線 (10.10.172.127)

```python
# Django settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ai_platform',
        'USER': 'postgres',
        'PASSWORD': 'postgres123',
        'HOST': '10.10.173.29',
        'PORT': '5432',
    }
}
```

### 從外部工具連線

- **Host**: `10.10.173.29`
- **Port**: `5432`
- **Database**: `ai_platform`
- **User**: `postgres`
- **Password**: `postgres123`

### Adminer Web 介面

瀏覽器訪問：`http://10.10.173.29:9090`
- 系統：PostgreSQL
- 服務器：`postgres`（或 `postgres_db`）
- 用戶名：`postgres`
- 密碼：`postgres123`
- 資料庫：`ai_platform`

## 🛠️ 故障排除

### 無法連線到資料庫

```bash
# 1. 檢查容器狀態
docker compose ps

# 2. 檢查 PostgreSQL 是否準備就緒
docker exec postgres_db pg_isready -U postgres

# 3. 檢查防火牆
sudo ufw status
sudo ufw allow 5432/tcp

# 4. 檢查日誌
docker logs postgres_db --tail 50
```

### pgvector 擴展問題

```bash
# 檢查擴展是否安裝
docker exec postgres_db psql -U postgres -d ai_platform -c "SELECT * FROM pg_extension;"

# 手動安裝擴展
docker exec postgres_db psql -U postgres -d ai_platform -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 資料 Volume 問題

```bash
# 查看 volume
docker volume ls | grep postgres

# 檢查 volume 詳情
docker volume inspect postgres-db-server_postgres_data

# 備份 volume（緊急情況）
docker run --rm -v postgres-db-server_postgres_data:/data -v $(pwd):/backup alpine tar cvf /backup/postgres_volume_backup.tar /data
```

## 📁 目錄結構

```
postgres-db-server/
├── docker-compose.yml     # Docker 服務配置
├── .env                   # 環境變數（不納入版本控制）
├── .env.example           # 環境變數範例
├── scripts/
│   └── init-pgvector.sql  # 資料庫初始化腳本
└── README.md              # 本文件
```

## 🔐 安全注意事項

1. **修改預設密碼**：生產環境請修改 `POSTGRES_PASSWORD`
2. **防火牆設定**：限制 5432 端口只允許特定 IP 訪問
3. **定期備份**：建議每日自動備份
4. **監控**：設定資源使用監控和告警

## 📞 支援

- **主專案位置**：`10.10.172.127:/home/user/codes/ai-platform-web`
- **遷移計畫文檔**：`docs/deployment/database-migration-plan.md`
- **維護者**：AI Platform Team

---

**最後更新**：2025-12-11
