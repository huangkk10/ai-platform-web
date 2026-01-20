# 🏷️ Beta 標籤功能設定指南

## 📝 功能說明

本專案已完成在 `develop` branch 顯示 "Beta" 標籤的功能，通過環境變數 `REACT_APP_DEPLOY_ENV` 控制。

### ✅ 已修改的檔案

1. **`frontend/src/components/Sidebar.js`**
   - 在 Logo 區域的 "AI Assistant" 旁邊顯示橙色 Beta 標籤

2. **`frontend/src/components/TopHeader.js`**
   - 在每個頁面標題旁邊顯示橙色 Beta 標籤

3. **`docker-compose.yml`**
   - 為 `react` 服務添加 `REACT_APP_DEPLOY_ENV=develop` 環境變數

---

## 🎯 顯示效果

### **develop branch (設定 `REACT_APP_DEPLOY_ENV=develop`)**

**Sidebar:**
```
🖼️ AI Assistant [Beta] ← 橙色標籤
```

**TopHeader (每個頁面):**
```
📄 Protocol RAG [Beta]
📄 RVT Assistant [Beta]
📄 Dashboard [Beta]
```

### **main branch (未設定或 `=production`)**

**Sidebar:**
```
🖼️ AI Assistant
```

**TopHeader:**
```
📄 Protocol RAG
📄 Dashboard
```

---

## 🚀 部署步驟

### **在 develop branch (顯示 Beta 標籤)**

```bash
# 1. 確認當前在 develop branch
git branch

# 2. 重新 build 前端容器（會注入環境變數）
docker compose build ai-react

# 3. 重啟前端容器
docker compose up -d ai-react

# 4. 檢查環境變數是否正確
docker exec ai-react printenv | grep REACT_APP_DEPLOY_ENV
# 應該輸出: REACT_APP_DEPLOY_ENV=develop

# 5. 清除瀏覽器快取並重新整理
# 按 Ctrl+Shift+R (Windows/Linux) 或 Cmd+Shift+R (Mac)
```

### **在 main branch (不顯示 Beta 標籤)**

```bash
# 1. 切換到 main branch
git checkout main

# 2. 修改 docker-compose.yml，移除或註解 REACT_APP_DEPLOY_ENV
# 或者改為 REACT_APP_DEPLOY_ENV=production

# 3. 重新 build 和啟動
docker compose build ai-react
docker compose up -d ai-react
```

---

## 🔧 手動設定方式（不修改 docker-compose.yml）

### **方法 1：使用 .env 檔案**

在 `frontend/` 目錄創建 `.env` 或 `.env.development`：

```bash
# frontend/.env.development
REACT_APP_DEPLOY_ENV=develop
```

然後重新 build：
```bash
cd frontend
npm run build
```

### **方法 2：Build 時手動注入**

```bash
cd frontend
REACT_APP_DEPLOY_ENV=develop npm run build
```

### **方法 3：Docker Build Args**

```bash
docker build \
  --build-arg REACT_APP_DEPLOY_ENV=develop \
  -t ai-react:develop \
  ./frontend
```

---

## 🧪 測試驗證

### **驗證環境變數**

```bash
# 在容器內檢查
docker exec ai-react printenv | grep REACT_APP

# 或者在前端 Console 中執行
console.log('Deploy Env:', process.env.REACT_APP_DEPLOY_ENV);
```

### **預期結果**

✅ **develop 環境**：
- Logo 旁顯示橙色 "Beta" 標籤
- 每個頁面標題旁顯示橙色 "Beta" 標籤
- Console 輸出: `Deploy Env: develop`

✅ **production/main 環境**：
- 沒有顯示任何 Beta 標籤
- Console 輸出: `Deploy Env: undefined` 或 `production`

---

## 📊 Branch 差異管理

### **統一程式碼，不同環境**

**重要優點**：
- ✅ `develop` 和 `main` branch 的程式碼**完全相同**
- ✅ 只有 `docker-compose.yml` 的環境變數不同
- ✅ 不會產生 merge conflict
- ✅ 易於維護和部署

### **建議的 Git Workflow**

```bash
# develop branch - docker-compose.yml
environment:
  - REACT_APP_DEPLOY_ENV=develop  # ← 保留這行

# main branch - docker-compose.yml
environment:
  # - REACT_APP_DEPLOY_ENV=develop  # ← 註解或移除這行
  # 或者改為:
  - REACT_APP_DEPLOY_ENV=production
```

---

## 🎨 自訂樣式（可選）

如果想要修改 Beta 標籤的樣式，可以編輯以下檔案：

### **Sidebar.js (行 ~488)**
```javascript
<Tag color="orange" style={{ 
  fontSize: '11px', 
  padding: '0 6px', 
  marginTop: '2px' 
}}>
  Beta
</Tag>
```

### **TopHeader.js (行 ~156)**
```javascript
<Tag color="orange" style={{ 
  fontSize: '11px', 
  padding: '0 6px' 
}}>
  Beta
</Tag>
```

**可調整參數**：
- `color`: `orange` | `red` | `blue` | `green` | `purple`
- `fontSize`: 字體大小
- `padding`: 內距
- 標籤文字: `Beta` → 可改為其他文字（如 `DEV`, `測試版` 等）

---

## 🐛 故障排除

### **問題 1：修改後看不到 Beta 標籤**

**解決方案**：
```bash
# 1. 確認環境變數
docker exec ai-react printenv | grep REACT_APP_DEPLOY_ENV

# 2. 如果沒有輸出，需要重新 build
docker compose build ai-react
docker compose up -d ai-react

# 3. 清除瀏覽器快取
按 Ctrl+Shift+R (硬重新整理)
```

### **問題 2：main branch 也顯示 Beta 標籤**

**解決方案**：
- 檢查 `main` branch 的 `docker-compose.yml`
- 確認 `REACT_APP_DEPLOY_ENV` 沒有設為 `develop`
- 或者將其設為 `production`

### **問題 3：Build 時沒有注入環境變數**

**解決方案**：
```bash
# 確認 docker-compose.yml 的 build args
docker compose config | grep -A 5 "react:"

# 應該看到:
# args:
#   REACT_APP_DEPLOY_ENV: develop
```

---

## 📚 相關文件

- **前端組件**：
  - `frontend/src/components/Sidebar.js`
  - `frontend/src/components/TopHeader.js`

- **Docker 配置**：
  - `docker-compose.yml`

- **環境變數文件**（可選）：
  - `frontend/.env.development`
  - `frontend/.env.production`

---

## 🎉 完成！

現在你的 `develop` branch 會自動顯示 Beta 標籤，而 `main` branch 則顯示正常版本。

如有任何問題，請參考上方的故障排除章節或聯繫開發團隊。

---

**更新日期**: 2026-01-19  
**版本**: v1.0  
**作者**: AI Assistant Team
