# Docker 安裝腳本使用說明

## 檔案位置
`scripts/install-docker.sh`

## 功能
自動安裝 Docker CE 及相關組件，包含：
- Docker CE (Container Engine)
- Docker CLI (命令列工具)
- containerd.io (容器運行時)
- Docker Buildx Plugin (擴展建構功能)
- **Docker Compose Plugin v2** (多容器應用管理)

> **注意**: 新版 Docker 安裝會自動包含 Docker Compose Plugin v2，使用 `docker compose` 命令（注意是空格，不是破折號）。

## 使用方法

### 1. 給予執行權限
```bash
chmod +x scripts/install-docker.sh
```

### 2. 執行安裝
```bash
./scripts/install-docker.sh
```

### 3. 完成後重新載入群組權限
```bash
# 選擇其中一種方式：
newgrp docker
# 或
exec su - $USER
# 或重新登入終端
```

### 4. 測試安裝
```bash
docker run hello-world
docker --version
docker compose version
```

### 5. Docker Compose 使用範例
```bash
# 檢查 Docker Compose 版本
docker compose version

# 基本 Docker Compose 命令
docker compose up          # 啟動服務
docker compose up -d       # 背景啟動服務
docker compose down        # 停止並移除服務
docker compose ps          # 列出服務狀態
docker compose logs        # 查看日誌
docker compose restart     # 重啟服務
```

## 安裝步驟詳解
1. 更新套件清單並安裝依賴
2. 新增 Docker 官方 GPG key
3. 新增 Docker repository
4. 安裝 Docker CE 及相關組件
5. 啟動並啟用 Docker 服務
6. 將使用者加入 docker 群組
7. 驗證安裝結果

## 系統需求
- Ubuntu 18.04+ 或 Debian 10+
- 有 sudo 權限的使用者帳號
- 網路連線 (下載套件)

## 安全性
- 腳本會檢查不允許以 root 執行
- 使用官方 Docker repository
- 啟用 `set -e` 確保錯誤時停止執行

## 注意事項
- 安裝後需要重新登入或執行 `newgrp docker` 才能不用 sudo 執行 docker
- 腳本主要針對 Ubuntu/Debian 系統設計
- 如果 Docker 已安裝，建議先移除舊版本

## 故障排除
如果遇到權限問題：
```bash
# 檢查使用者是否在 docker 群組
groups

# 檢查 docker 群組
getent group docker

# 重新載入群組
newgrp docker
```

## Docker Compose 詳細說明

### 什麼是 Docker Compose？
Docker Compose 是一個用於定義和運行多容器 Docker 應用程式的工具。使用 YAML 檔案來配置應用程式的服務。

### 版本差異
- **Docker Compose v1** (舊版): 使用 `docker-compose` 命令（需要單獨安裝）
- **Docker Compose v2** (新版): 使用 `docker compose` 命令（內建於 Docker 中）

我們的安裝腳本會安裝 Docker Compose v2，這是目前推薦的版本。

### 基本用法
1. **建立 docker-compose.yml 檔案**:
```yaml
version: '3.8'
services:
  web:
    image: nginx:latest
    ports:
      - "8080:80"
  database:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: password
```

2. **執行應用程式**:
```bash
# 啟動所有服務
docker compose up

# 背景啟動
docker compose up -d

# 停止服務
docker compose down

# 查看服務狀態
docker compose ps

# 查看日誌
docker compose logs

# 重新建構並啟動
docker compose up --build
```

### 常用命令速查表
```bash
docker compose up              # 建立並啟動容器
docker compose up -d           # 背景模式啟動
docker compose down            # 停止並移除容器
docker compose down -v         # 停止並移除容器及 volumes
docker compose restart         # 重啟服務
docker compose pull            # 拉取最新映像檔
docker compose build           # 建構映像檔
docker compose ps              # 列出服務
docker compose logs            # 查看所有服務日誌
docker compose logs web        # 查看特定服務日誌
docker compose exec web bash   # 在 web 服務中執行 bash
```

### 如果需要 Docker Compose v1
如果你的專案需要舊版的 `docker-compose` 命令：
```bash
# 安裝 Docker Compose v1 (standalone)
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 驗證安裝
docker-compose --version
```