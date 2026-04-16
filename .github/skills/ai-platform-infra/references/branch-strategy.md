# Git 分支策略與部署流程

## Branch 對應環境

| Branch | 環境 | 主機 | 說明 |
|--------|------|------|------|
| **`develop`** | **開發機** | `10.10.172.127` | ⭐ 日常開發，測試新功能 |
| **`main`** | **生產機** | `10.10.172.123` (DB) + `10.10.172.127` (Web) | 穩定版本 |
| `feature/*` | 個人功能 | — | 完成後 merge 回 develop |

> ✅ **這台 PC 是開發機 → 使用 `develop` branch**

---

## develop branch 的特殊設定

`docker-compose.override.yml` **只存在於 develop branch**，會自動：
- 前端 React 顯示橙色 **Beta** 標籤（Sidebar + TopHeader）
- 注入 `REACT_APP_DEPLOY_ENV=develop`

```bash
# develop 啟動（自動使用 override）
docker compose up -d
```

main branch 沒有 `docker-compose.override.yml`，不會顯示 Beta 標籤。

---

## Dify API Keys 對應

| Branch | Dify App 類型 | 連接的外部知識庫 API |
|--------|--------------|---------------------|
| `develop` | `*_dev` 後綴 App | `10.10.172.127`（開發機） |
| `main` | 正式命名 App | `10.10.172.123`（生產機 DB） |

設定位置：`library/config/dify_config_manager.py`  
環境判斷：`DIFY_ENV=development`（docker-compose.yml 中設定）

---

## 切換 Branch

```bash
# 切換到開發 branch
git checkout develop

# 切換到生產 branch
git checkout main
```

---

## develop → main 合併流程（生產部署）

```bash
# 1. 確認 develop 測試完成，在 main branch 上操作
git checkout main
git status  # 確認 working tree clean

# 2. 合併
git merge develop

# 3. 推送
git push origin main

# 4. 生產機重新部署
docker compose up -d --build
python manage.py migrate  # 如有新 migration
python manage.py collectstatic --noinput
```

### 合併前檢查清單

- [ ] develop 功能已完整測試
- [ ] 所有測試通過
- [ ] Migration 檔案已 commit
- [ ] 生產環境資料庫已備份

---

## 目前 Branch 狀態（最後更新 2026-04-16）

| Branch | 最新 commit |
|--------|-------------|
| `develop` | `3e5d8e9` — chore: 添加 Beta Badge 驗證腳本 |
| `main` | `90ee117` — chore: merge develop → main - Protocol RAG 修正 |

> `develop` 比 `main` 多 1 個 commit（develop 超前）

---

## 現有 Branches

| Branch | 說明 |
|--------|------|
| `develop` | 主要開發分支 |
| `main` | 生產分支 |
| `feature/search-version-toggle` | 搜尋版本切換功能 |
| `new_feature` | 新功能開發 |
| `debug_protocol` | Protocol 除錯 |
| `context_window` | Context window 相關 |
| `backup/conversation-id-testing-20251106` | 備份分支 |
