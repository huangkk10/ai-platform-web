# Docker Compose Override 配置說明

## 📋 概述

本專案使用 **docker-compose.override.yml** 來區分 develop 和 main 環境，避免在 `docker-compose.yml` 中直接寫入環境特定的配置。

## 🏗️ 架構設計

### 檔案分工

| 檔案 | 用途 | Branch |
|------|------|--------|
| `docker-compose.yml` | 基礎配置（兩個 branch 相同） | develop + main |
| `docker-compose.override.yml` | Develop 環境專用覆蓋設定 | **僅 develop** |

### Docker Compose 自動合併機制

當執行 `docker compose up` 時，Docker Compose 會自動：
1. 讀取 `docker-compose.yml`（基礎配置）
2. 如果存在 `docker-compose.override.yml`，自動合併覆蓋設定
3. 無需額外參數，自動生效

## 🔧 Develop 環境配置

### docker-compose.override.yml（僅存在於 develop branch）

```yaml
services:
  react:
    build:
      args:
        - REACT_APP_DEPLOY_ENV=develop
    environment:
      - REACT_APP_DEPLOY_ENV=develop
```

**效果**：
- ✅ 前端顯示橙色 "Beta" 標籤（Sidebar 和 TopHeader）
- ✅ 可在程式碼中檢測環境：`process.env.REACT_APP_DEPLOY_ENV === 'develop'`

## 🚀 部署流程

### Develop 環境（當前）

```bash
# 正常啟動，會自動使用 override 檔案
docker compose up -d

# 或重建容器
docker compose up -d --build
```

### Main 環境（Production）

```bash
# 確保沒有 docker-compose.override.yml
# 正常啟動即可（不會顯示 Beta 標籤）
docker compose up -d
```

## 📂 Branch 管理策略

### Develop Branch
```
ai-platform-web/
├── docker-compose.yml           ✅ 基礎配置（無環境特定設定）
├── docker-compose.override.yml  ✅ Develop 專用（顯示 Beta）
└── frontend/
    └── src/components/
        ├── Sidebar.js           ✅ 包含 Beta 標籤邏輯
        └── TopHeader.js         ✅ 包含 Beta 標籤邏輯
```

### Main Branch
```
ai-platform-web/
├── docker-compose.yml           ✅ 基礎配置（與 develop 相同）
├── docker-compose.override.yml  ❌ 不存在！
└── frontend/
    └── src/components/
        ├── Sidebar.js           ✅ 包含 Beta 標籤邏輯（但不顯示）
        └── TopHeader.js         ✅ 包含 Beta 標籤邏輯（但不顯示）
```

## 🔄 合併到 Main Branch 的流程

### 步驟 1：合併程式碼（保留 Beta 邏輯）
```bash
git checkout main
git merge develop  # docker-compose.yml 不會衝突！
```

### 步驟 2：確保 main 沒有 override 檔案
```bash
# 在 main branch 中
git rm docker-compose.override.yml  # 如果誤合併了
git commit -m "remove: 移除 develop 專用的 override 配置"
```

### 步驟 3：部署 main 環境
```bash
docker compose down
docker compose up -d --build
# 此時不會顯示 Beta 標籤（因為沒有 REACT_APP_DEPLOY_ENV 變數）
```

## ✅ 驗證環境差異

### 檢查 Develop 環境
```bash
# 檢查檔案存在
ls -la docker-compose.override.yml

# 檢查環境變數
docker exec ai-react printenv | grep REACT_APP_DEPLOY_ENV
# 應該輸出：REACT_APP_DEPLOY_ENV=develop
```

### 檢查 Main 環境
```bash
# 檢查檔案不存在
ls -la docker-compose.override.yml
# 應該輸出：No such file or directory

# 檢查環境變數（應該沒有）
docker exec ai-react printenv | grep REACT_APP_DEPLOY_ENV
# 無輸出或空白
```

## 📊 優勢對比

| 項目 | 舊方案（修改 docker-compose.yml） | 新方案（Override 檔案） |
|------|-----------------------------------|------------------------|
| 程式碼一致性 | ❌ develop/main 的 yml 不同 | ✅ yml 完全相同 |
| 合併衝突 | ❌ 每次合併都會衝突 | ✅ 不會衝突 |
| 維護成本 | ❌ 需手動處理環境差異 | ✅ 自動處理 |
| 錯誤風險 | ❌ 容易忘記修改 | ✅ 檔案存在即生效 |
| 部署複雜度 | 中等 | ✅ 簡單（自動合併） |

## 🎯 最佳實踐

1. **Develop Branch**：保留 `docker-compose.override.yml`，commit 到版本控制
2. **Main Branch**：確保沒有 `docker-compose.override.yml`
3. **程式碼邏輯**：Beta 標籤邏輯保留在 Sidebar.js 和 TopHeader.js（兩個 branch 相同）
4. **環境控制**：完全由 `docker-compose.override.yml` 的存在與否決定

## 🔍 故障排除

### 問題：Main 仍然顯示 Beta
**原因**：可能誤將 `docker-compose.override.yml` 合併到 main

**解決**：
```bash
git checkout main
git rm docker-compose.override.yml
git commit -m "fix: 移除 develop 專用配置"
docker compose down
docker compose up -d --build
```

### 問題：Develop 沒有顯示 Beta
**原因**：`docker-compose.override.yml` 可能不存在或格式錯誤

**解決**：
```bash
# 確認檔案存在
cat docker-compose.override.yml

# 重建容器
docker compose down
docker compose up -d --build
```

---

**更新日期**：2026-01-19  
**版本**：v2.0（使用 Override 檔案方案）  
**適用環境**：Docker Compose v2.x
