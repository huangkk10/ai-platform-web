# AI Platform Web - RVT Assistant 系統

## 🚀 **重要功能亮點**

### 🤖 **RVT Assistant 智慧分析報告系統** ⭐ **NEW**  
- **實施日期**: 2025-10-13
- **狀態**: ✅ 已上線並優化
- **特色**: 三種分析模式 + 智慧自動選擇最佳分析方式
- **解決問題**: 聚類演算法掩蓋高頻問題（如UCC問題排名）

**核心創新**:
- 🤖 **智慧分析模式**: 自動檢測聚類問題並選擇最佳分析方式
- 📊 **三種模式**: 聚類分析 / 原始頻率 / 智慧選擇
- ⚡ **即時修正**: 發現聚類掩蓋問題時自動切換到頻率統計
- 🎯 **準確排名**: 確保熱門問題（如"ucc 是什麼" 23次）正確顯示

**實際效果**:
- ✅ 解決了 UCC 問題被聚類掩蓋的問題
- ✅ "ucc 是什麼" 從被隱藏 → 正確顯示為 #1 熱門問題
- ✅ 智慧檢測到 3個高頻問題差異，自動切換分析模式

### 🤖 **RVT Assistant 向量資料庫定時更新架構**
- **實施日期**: 2025-10-09
- **狀態**: ✅ 已驗證並運行  
- **設計**: 使用 Celery Beat 定時任務批量處理向量化
- **效果**: 向量化率從 8.1% 提升到 30.6%

**核心特色**:
- 每小時自動處理用戶問題向量化  
- 智能去重機制，避免重複處理
- 批量處理效率 (~5 消息/秒)
- 不影響聊天功能穩定性

**快速檢查**: 
```bash
# 檢查向量化率
docker exec ai-django python -c "
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('SELECT COUNT(*) FROM chat_messages'); total = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM chat_message_embeddings_1024'); vectorized = cursor.fetchone()[0]
    print(f'向量化率: {vectorized/total*100:.1f}%')
"
```

**詳細文檔**: 
- 📖 [完整架構文檔](docs/vector-database-scheduled-update-architecture.md)
- 📋 [快速參考指南](docs/vector-update-quick-reference.md)  
- 🤖 [AI 協助指導](docs/ai-guidance-vector-architecture.md)

---

## 🚀 **生產環境部署流程**

### 📋 **將 develop 分支合併到 main（生產機部署）**

當開發環境測試完成，需要將新功能部署到生產機時，請按照以下步驟操作：

#### **前置準備**
- ✅ 確認開發環境功能已完整測試
- ✅ 確認所有測試通過
- ✅ 確認資料庫 Migration 檔案已提交到 Git
- ✅ 備份生產環境資料庫（建議）

---

#### **步驟 1️⃣：Git 合併操作**

```bash
# 確認當前狀態
git status
# 輸出應顯示：On branch main, working tree clean

# 確認在 main 分支且工作目錄乾淨
git branch
# 應該顯示 * main

# 將 develop 分支合併到 main
git merge develop

# 如果有衝突，解決衝突後執行
git add .
git commit -m "chore: merge develop into main"
```

**說明**：
- 確保在 `main` 分支上操作
- 合併前確認 working tree 乾淨（無未提交的變更）
- 如果使用 Pull Request 方式，在 GitHub 上操作後再 `git pull origin main`

---

#### **步驟 2️⃣：資料庫遷移**

```bash
# 執行資料庫 Migration（⚠️ 重要！）
docker exec ai-django python manage.py migrate

# 檢查 Migration 狀態
docker exec ai-django python manage.py showmigrations
```

**說明**：
- ⚠️ **此步驟必須執行**：即使程式碼已更新，資料庫架構不會自動更新
- Migration 檔案會隨程式碼一起合併，但需要手動執行 `migrate` 才會套用到資料庫
- 檢查 `showmigrations` 確認所有 Migration 都已執行（顯示 `[X]`）

---

#### **步驟 3️⃣：重啟 Docker 服務**

```bash
# 停止所有容器
docker compose down

# 重新啟動所有容器
docker compose up -d

# 檢查容器狀態
docker compose ps

# 查看服務日誌（確認無錯誤）
docker compose logs -f django
```

**說明**：
- 重啟服務以載入新的程式碼
- 使用 `-d` 參數讓容器在背景執行
- 檢查日誌確認服務正常啟動

---

#### **步驟 4️⃣：推送到遠端**

```bash
# 推送 main 分支到遠端倉庫
git push origin main
```

**說明**：
- 將本地的 main 分支推送到 GitHub
- 確保遠端倉庫與生產環境同步

---

#### **步驟 5️⃣：驗證部署結果**

```bash
# 檢查 API 端點
curl http://localhost/api/

# 檢查資料庫連接
docker exec postgres_db psql -U postgres -d ai_platform -c "\dt"

# 檢查環境變數
docker exec ai-django env | grep -E "DEBUG|ENVIRONMENT"

# 測試關鍵功能
# 1. 訪問前端頁面
# 2. 測試 API 功能
# 3. 測試 AI 助手功能
```

---

### ✅ **部署檢查清單**

完成部署後，請確認以下項目：

- [ ] ✅ 程式碼已更新（`git status` 顯示最新 commit）
- [ ] ✅ 資料庫 Migration 已執行（`showmigrations` 全部顯示 `[X]`）
- [ ] ✅ 所有 Docker 容器正常運行（`docker compose ps` 無異常）
- [ ] ✅ 環境變數正確（`DEBUG=0`, `ENVIRONMENT=production`）
- [ ] ✅ API 端點可正常訪問
- [ ] ✅ 前端頁面可正常開啟
- [ ] ✅ 資料庫連接正常
- [ ] ✅ Dify AI 功能正常（測試聊天功能）
- [ ] ✅ 日誌無明顯錯誤
- [ ] ✅ 遠端倉庫已更新（`git push` 成功）

---

### ⚠️ **注意事項**

1. **資料庫 Migration 必須手動執行**
   - ❌ 錯誤：以為 `git merge` 就會自動更新資料庫
   - ✅ 正確：合併後還需執行 `python manage.py migrate`

2. **環境變數差異**
   - 開發機：`DEBUG=1`, `ENVIRONMENT=development`
   - 生產機：`DEBUG=0`, `ENVIRONMENT=production`
   - 透過 `docker-compose.override.yml` 或 `.env.prod` 設定

3. **資料庫是獨立的**
   - 開發機資料庫：`ai_platform_dev`（本機）
   - 生產機資料庫：`ai_platform`（本機）
   - 程式碼相同，但資料內容獨立

4. **建議使用 Pull Request**
   - 在 GitHub 上創建 PR：`develop` → `main`
   - Code Review 確保程式碼品質
   - 在 GitHub 上合併後，生產機執行 `git pull origin main`

---

### 🔗 **相關文檔**

- 📖 [開發/生產環境分離計畫](docs/deployment/dev-prod-environment-separation-plan.md)
- 🐳 [Docker 安裝指南](docs/deployment/docker-installation.md)
- 🗄️ [資料庫遷移指南](docs/deployment/database-migration-plan.md)