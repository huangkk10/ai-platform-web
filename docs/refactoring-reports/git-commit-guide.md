# Git Commit 建議

## 📋 建議的 Commit 訊息

```
refactor(frontend): 移除搜尋版本切換功能

移除 RVT Assistant 和 Protocol Assistant 的 V1/V2 搜尋版本切換開關。

經代碼審查發現，後端從未使用 search_version 參數，所有搜尋始終使用
相同的語義向量搜尋邏輯。前端的切換開關是誤導性的 UI 元素。

修改內容：
- 移除 useRvtChat.js 中的 searchVersion state 和 localStorage 邏輯
- 移除 useProtocolAssistantChat.js 中的 searchVersion state
- 移除 CommonAssistantChatPage.jsx 中的 SearchVersionToggle 組件渲染
- 固定發送 search_version: 'v2'（雖然後端會忽略此參數）
- 新增統一搜尋測試腳本 test_unified_search.sh
- 更新重構文檔

測試結果：
- 4/4 測試案例全部通過
- RVT Assistant 和 Protocol Assistant 功能正常
- UI 簡化，無 JavaScript 錯誤

影響：
- 移除 46 行代碼
- 簡化用戶界面（移除誤導性選項）
- 無功能變化（後端邏輯未改變）
- 減少技術債務

BREAKING CHANGE: 移除了前端的搜尋版本切換 UI，所有用戶將統一使用
語義搜尋（V2）。由於後端從未實現 V1/V2 差異，此變更不影響搜尋結果。

關閉議題：#N/A
參考文檔：docs/refactoring-reports/remove-search-version-toggle.md
```

---

## 📂 建議的檔案變更清單

### 修改的檔案
```
modified:   frontend/src/hooks/useRvtChat.js
modified:   frontend/src/hooks/useProtocolAssistantChat.js
modified:   frontend/src/components/chat/CommonAssistantChatPage.jsx
```

### 新增的檔案
```
new file:   test_unified_search.sh
new file:   docs/refactoring-reports/remove-search-version-toggle.md
new file:   docs/refactoring-reports/remove-search-version-toggle-summary.md
new file:   docs/refactoring-reports/remove-search-version-toggle-quick-ref.md
new file:   docs/refactoring-reports/git-commit-guide.md
```

### 可選刪除（未來）
```
# 這些檔案已不再使用，但暫時保留作為參考
frontend/src/components/chat/SearchVersionToggle.jsx
tests/test_search_version_toggle.py
backend/tests/test_search_version_toggle.py
```

---

## 🔧 Git 指令建議

### 檢查變更
```bash
git status
git diff frontend/src/hooks/useRvtChat.js
git diff frontend/src/hooks/useProtocolAssistantChat.js
git diff frontend/src/components/chat/CommonAssistantChatPage.jsx
```

### 分階段提交（推薦）

#### 提交 1：前端修改
```bash
git add frontend/src/hooks/useRvtChat.js
git add frontend/src/hooks/useProtocolAssistantChat.js
git add frontend/src/components/chat/CommonAssistantChatPage.jsx

git commit -m "refactor(frontend): 移除搜尋版本切換 UI

- 移除 useRvtChat.js 中的 searchVersion state (-15 行)
- 移除 useProtocolAssistantChat.js 中的 searchVersion state (-13 行)
- 移除 CommonAssistantChatPage.jsx 中的切換開關渲染 (-18 行)
- 固定發送 search_version: 'v2'（後端會忽略此參數）

測試：所有聊天功能正常運作"
```

#### 提交 2：測試和文檔
```bash
git add test_unified_search.sh
git add docs/refactoring-reports/remove-search-version-toggle*.md
git add docs/refactoring-reports/git-commit-guide.md

git commit -m "docs: 新增搜尋版本切換移除的測試和文檔

- 新增統一搜尋測試腳本（4 個測試案例，100% 通過）
- 新增詳細重構報告
- 新增總結報告和快速參考
- 說明後端實際上從未使用 search_version 參數"
```

### 單一提交（簡化版）
```bash
git add frontend/src/hooks/useRvtChat.js
git add frontend/src/hooks/useProtocolAssistantChat.js
git add frontend/src/components/chat/CommonAssistantChatPage.jsx
git add test_unified_search.sh
git add docs/refactoring-reports/remove-search-version-toggle*.md
git add docs/refactoring-reports/git-commit-guide.md

git commit -m "refactor: 移除搜尋版本切換功能 (V1/V2)

修改：移除前端 V1/V2 切換開關，統一使用語義搜尋
原因：後端從未使用 search_version 參數，切換開關是誤導性 UI
影響：-46 行代碼，簡化 UI，無功能變化
測試：4/4 案例通過，RVT 和 Protocol Assistant 正常運作"
```

---

## 🔀 分支建議

### 當前分支
```bash
# 檢查當前分支
git branch

# 預期：feature/search-version-toggle
```

### 合併到主分支
```bash
# 1. 確保所有變更已提交
git status

# 2. 推送到遠端
git push origin feature/search-version-toggle

# 3. 創建 Pull Request (GitHub/GitLab)
# 標題：refactor: 移除搜尋版本切換功能
# 描述：參考 docs/refactoring-reports/remove-search-version-toggle-summary.md

# 4. 合併後刪除功能分支
git branch -d feature/search-version-toggle
git push origin --delete feature/search-version-toggle
```

---

## 📝 Pull Request 範本

```markdown
## 🎯 變更摘要
移除 RVT Assistant 和 Protocol Assistant 的 V1/V2 搜尋版本切換開關。

## 🔍 問題說明
經代碼審查發現，後端從未使用 `search_version` 參數，所有搜尋始終使用相同的語義向量搜尋邏輯。前端的切換開關是誤導性的 UI 元素。

## 🔧 解決方案
- 移除前端的 searchVersion state 管理
- 移除 SearchVersionToggle UI 組件渲染
- 固定發送 `search_version: 'v2'`（雖然後端會忽略）
- 簡化用戶界面

## ✅ 測試
- [x] 所有單元測試通過
- [x] 整合測試通過（4/4 案例）
- [x] RVT Assistant 功能正常
- [x] Protocol Assistant 功能正常
- [x] 無 JavaScript 錯誤
- [x] UI 正確顯示（無切換開關）

## 📊 影響分析
- **代碼量**: -46 行
- **UI 組件**: -1 個
- **功能變化**: 無（後端邏輯未改變）
- **用戶體驗**: 改善（移除誤導性選項）

## 📚 文檔
- [完整重構報告](docs/refactoring-reports/remove-search-version-toggle.md)
- [總結報告](docs/refactoring-reports/remove-search-version-toggle-summary.md)
- [快速參考](docs/refactoring-reports/remove-search-version-toggle-quick-ref.md)

## 🚀 部署注意事項
需要執行前端構建：
```bash
cd frontend && npm run build
docker compose restart ai-react
```

## 📸 截圖
（可選：添加移除切換開關前後的 UI 對比圖）

## ✍️ 審核者注意事項
- 檢查 UI 中確實沒有顯示切換開關
- 驗證聊天功能正常運作
- 確認測試腳本全部通過
```

---

## 🎓 Commit Message 最佳實踐

### Type 選擇指南
- `refactor`: ✅ **推薦** - 代碼重構，無功能變化
- `feat`: ❌ 不適用 - 這不是新功能
- `fix`: ❌ 不適用 - 這不是修復 bug
- `chore`: ⚠️ 可接受 - 但 refactor 更準確

### Scope 選擇
- `frontend`: ✅ 主要變更在前端
- `ui`: ✅ UI 組件移除
- `search`: ⚠️ 容易誤解為搜尋功能變更

### 推薦格式
```
refactor(frontend): 移除搜尋版本切換功能

或

refactor(ui): 移除 RVT/Protocol Assistant 的 V1/V2 切換開關
```

---

## 🔖 標籤建議

如果使用 Git 標籤管理版本：
```bash
git tag -a v1.5.0-search-simplification -m "移除搜尋版本切換功能"
git push origin v1.5.0-search-simplification
```

---

**創建日期**: 2025-11-10  
**更新日期**: 2025-11-10  
**版本**: 1.0
