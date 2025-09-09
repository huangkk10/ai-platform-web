# Git Commit Type

請遵守下列 commit type（Conventional Commits 為基礎）：

- feat: 新增/修改功能 (feature)。
- fix: 修補 bug (bug fix)。
- docs: 文件 (documentation)。
- style: 格式 (不影響程式碼運行的變動 white-space, formatting, missing semi colons, etc)。
- refactor: 重構 (既不是新增功能，也不是修補 bug 的程式碼變動)。
- perf: 改善效能 (A code change that improves performance)。
- test: 增加測試 (when adding missing tests)。
- chore: 建構程序或輔助工具的變動 (maintain)。
- revert: 撤銷回覆先前的 commit 例如：revert: type(scope): subject (回覆版本：xxxx)。
- vert: 進版（版本相關變更）。

System prompt（AI 專用簡短提示）：

你是一個 commit message 建議工具，回傳 JSON 與 2 個可選的 commit messages，並遵守上面的 type 列表。格式：<type>(optional-scope): <subject>。subject 最多 72 字元；需要說明放 body；breaking change 在 footer 使用 `BREAKING CHANGE:`。不要包含任何敏感資訊或憑證。


# 遠端 PC 操作指引（AI 專用）

## 重要安全警告
⚠️ **此檔案包含敏感連線資訊，僅供內部 AI 工具參考。請勿將此檔案推送至公開 repository 或分享給未授權人員。**

## 遠端主機資訊
- **使用者**：user
- **密碼**：1234
- **IP 位址**：10.10.173.12
- **連線方式**：SSH

## AI Platform 系統資訊

### 服務架構
- **前端 (React)**：Port 3000 (開發)，透過 Nginx Port 80 對外
- **後端 (Django)**：Port 8000，提供 REST API
- **資料庫 (PostgreSQL)**：Port 5432
- **反向代理 (Nginx)**：Port 80/443
- **容器管理 (Portainer)**：Port 9000
- **資料庫管理 (Adminer)**：Port 9090

### 資料庫連接資訊
- **資料庫類型**：PostgreSQL 15-alpine
- **容器名稱**：postgres_db
- **資料庫名稱**：ai_platform
- **用戶名**：postgres
- **密碼**：postgres123
- **外部連接**：localhost:5432 (從主機連接)
- **內部連接**：postgres_db:5432 (容器間通信)

### Web 管理介面
- **主要應用**：http://10.10.173.12 (Nginx 代理)
- **Adminer 資料庫管理**：http://10.10.173.12:9090
  - 系統：PostgreSQL
  - 服務器：postgres_db
  - 用戶名：postgres
  - 密碼：postgres123
- **Portainer 容器管理**：http://10.10.173.12:9000
- **Django Admin**：http://10.10.173.12/admin/
- **API 端點**：http://10.10.173.12/api/

### Docker 容器狀態
- **ai-nginx**：Nginx 反向代理
- **ai-react**：React 前端開發服務器
- **ai-django**：Django 後端 API 服務
- **postgres_db**：PostgreSQL 主資料庫
- **adminer_nas**：Adminer 資料庫管理工具
- **portainer**：Docker 容器管理工具

### 開發環境路徑
- **專案根目錄**：/home/user/codes/ai-platform-web
- **前端代碼**：/home/user/codes/ai-platform-web/frontend
- **後端代碼**：/home/user/codes/ai-platform-web/backend
- **Nginx 配置**：/home/user/codes/ai-platform-web/nginx
- **文檔目錄**：/home/user/codes/ai-platform-web/docs

### 常用指令
```bash
# 檢查所有容器狀態
docker compose ps

# 重新啟動特定服務
docker compose restart [service_name]

# 查看服務日誌
docker logs [container_name] --follow

# 進入容器
docker exec -it [container_name] bash

# 執行 Django 指令
docker exec -it ai-django python manage.py [command]

# 資料庫備份
docker exec postgres_db pg_dump -U postgres ai_platform > backup.sql
```

### API 認證狀態
- **當前狀態**：API 需要認證 (HTTP 403 為正常狀態)
- **Token 認證**：支援 DRF Token Authentication
- **Session 認證**：支援 Django Session Authentication
- **CORS 設定**：已配置跨域請求支援

### 系統狀態檢查
- **前後端整合**：✅ 正常運行
- **資料庫連接**：✅ PostgreSQL 健康運行
- **API 服務**：✅ Django REST Framework 正常
- **反向代理**：✅ Nginx 正確轉發請求
- **容器編排**：✅ Docker Compose 所有服務運行中


