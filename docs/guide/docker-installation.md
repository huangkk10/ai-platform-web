# Docker 安裝腳本使用說明

## 檔案位置
`scripts/install-docker.sh`

## 功能
自動安裝 Docker CE 及相關組件，包含：
- Docker CE (Container Engine)
- Docker CLI (命令列工具)
- containerd.io (容器運行時)
- Docker Buildx Plugin (擴展建構功能)
- Docker Compose Plugin (多容器應用管理)

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