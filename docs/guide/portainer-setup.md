# Portainer Docker Compose 使用說明

## 什麼是 Portainer？
Portainer 是一個輕量級的 Docker 管理 UI，提供簡單易用的網頁界面來管理 Docker 容器、映像檔、網路和儲存卷。

## 功能特色
- 🖥️ 網頁界面管理 Docker
- 📊 容器狀態監控
- 📝 容器日誌查看
- 🔧 容器管理（啟動、停止、重啟、刪除）
- 📦 映像檔管理
- 🌐 網路管理
- 💾 儲存卷管理
- 👥 使用者權限管理

## 快速啟動

### 1. 啟動 Portainer
```bash
# 在專案根目錄執行
docker compose up -d

# 查看服務狀態
docker compose ps

# 查看日誌
docker compose logs portainer
```

### 2. 訪問 Portainer
開啟瀏覽器並訪問：
- **HTTP**: http://localhost:9000
- **HTTPS**: https://localhost:9443

### 3. 初次設定
1. 第一次訪問時會要求建立管理員帳號
2. 設定使用者名稱和密碼（密碼至少 12 字元）
3. 選擇 "Docker" 作為環境類型
4. Portainer 會自動連接到本地 Docker

## 服務配置說明

### 連接埠
- **9000**: HTTP 連接埠
- **9443**: HTTPS 連接埠

### Volume 掛載
- `/var/run/docker.sock`: Docker socket（用於與 Docker daemon 通訊）
- `/etc/localtime`: 系統時間同步
- `portainer_data`: Portainer 資料持久化儲存

### 安全設定
- `no-new-privileges:true`: 防止容器獲得新的特權
- `restart: unless-stopped`: 除非手動停止，否則自動重啟

## 常用管理命令

```bash
# 啟動服務
docker compose up -d

# 停止服務
docker compose down

# 重啟服務
docker compose restart

# 查看服務狀態
docker compose ps

# 查看日誌
docker compose logs -f portainer

# 更新 Portainer
docker compose pull
docker compose up -d

# 完全清除（包含資料）
docker compose down -v
```

## 進階配置

### 啟用 HTTPS 自簽證書
如果需要使用自簽 SSL 證書，可以添加以下 command：
```yaml
command: --ssl --sslcert /data/portainer.crt --sslkey /data/portainer.key
```

### 連接外部 Docker 主機
如果要管理遠端 Docker 主機，可以在 Portainer 界面中添加 endpoints。

### 資料備份
Portainer 資料儲存在 `portainer_data` volume 中：
```bash
# 備份資料
docker run --rm -v portainer_data:/data -v $(pwd):/backup ubuntu tar czf /backup/portainer-backup.tar.gz /data

# 還原資料
docker run --rm -v portainer_data:/data -v $(pwd):/backup ubuntu tar xzf /backup/portainer-backup.tar.gz -C /
```

## 故障排除

### 無法訪問界面
1. 檢查容器是否正在運行：`docker compose ps`
2. 檢查連接埠是否被佔用：`netstat -tlnp | grep 9000`
3. 檢查防火牆設定

### 無法連接 Docker
1. 確認 Docker socket 權限正確
2. 檢查使用者是否在 docker 群組中：`groups`

### 密碼重設
如果忘記管理員密碼：
```bash
# 停止服務
docker compose down

# 清除資料重新開始
docker volume rm ai-platform-web_portainer_data

# 重新啟動
docker compose up -d
```

## 安全建議
1. 設定強密碼（至少 12 字元，包含大小寫字母、數字、特殊符號）
2. 如果要對外開放，建議使用反向代理（如 Nginx）
3. 定期更新 Portainer 版本
4. 限制網路存取（如使用防火牆規則）