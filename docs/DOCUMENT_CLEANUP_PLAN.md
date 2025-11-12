# 📁 文檔清理與重新組織計畫

## 🎯 目標
根據 `docs/ai_instructions.md` 中定義的 8 大文檔分類標準，將根目錄散落的 Markdown 文檔移至適當位置。

---

## 📊 文檔分析與分類建議

### ✅ **保留並移動到 `docs/` 的重要文檔**

#### 1. **`docs/debugging/` - 除錯與問題分析**
> 用途：系統問題調查、根因分析、故障排查

| 文檔 | 大小 | 移動路徑 | 優先級 | 原因 |
|------|------|---------|--------|------|
| `SAME_QUERY_DIFFERENT_RESULTS_ROOT_CAUSE.md` | 12K | `docs/debugging/` | ⭐⭐⭐⭐⭐ | **核心問題分析**，詳細解釋 Layer 3 機制 |
| `DIFY_AI_LAYER3_SELECTION_MECHANISM_ANALYSIS.md` | 30K | `docs/debugging/` | ⭐⭐⭐⭐⭐ | **最詳盡的技術分析**，包含數學模型 |
| `WHERE_IS_LAYER3_SELECTION.md` | 22K | `docs/debugging/` | ⭐⭐⭐⭐⭐ | **架構說明**，解答「Layer 3 在哪裡」 |
| `WEB_FAILURE_ROOT_CAUSE_ANALYSIS.md` | 17K | `docs/debugging/` | ⭐⭐⭐⭐ | Web UI 失敗原因分析 |
| `USER_HYPOTHESIS_ANALYSIS.md` | 13K | `docs/debugging/` | ⭐⭐⭐⭐ | 用戶假設驗證過程 |
| `CONVERSATION_MEMORY_PARADOX_EXPLAINED.md` | 11K | `docs/debugging/` | ⭐⭐⭐⭐ | 對話記憶矛盾解釋 |
| `MEMORY_INTERVAL_THEORY_CORRECTION.md` | 12K | `docs/debugging/` | ⭐⭐⭐ | 記憶間隔理論修正 |
| `TEST_VS_WEB_SAME_CONVERSATION_ID_PARADOX.md` | 14K | `docs/debugging/` | ⭐⭐⭐ | 測試環境與 Web 差異分析 |
| `WEB_VS_TEST_API_SETTINGS_COMPARISON.md` | 8.4K | `docs/debugging/` | ⭐⭐⭐ | API 設定比較 |
| `WEB_NEW_CHAT_BUTTON_BEHAVIOR.md` | 11K | `docs/debugging/` | ⭐⭐ | Web UI 新聊天按鈕行為 |
| `CUP_ISSUE_SUMMARY.md` | 6.9K | `docs/debugging/` | ⭐⭐ | CUP 問題總結（特定問題） |

---

#### 2. **`docs/development/` - 開發指南與規範**
> 用途：開發規範、操作指南、快速參考

| 文檔 | 大小 | 移動路徑 | 優先級 | 原因 |
|------|------|---------|--------|------|
| `LAYER3_STABILITY_IMPROVEMENT_PLAN.md` | 26K | `docs/development/` | ⭐⭐⭐⭐⭐ | **重要規劃文檔**，包含多個改進方案 |
| `KEYWORD_CLEANING_QUICK_REF.md` | 2.8K | `docs/development/` | ⭐⭐⭐ | 快速參考指南 |
| `GIT_COMMIT_SUGGESTION.md` | 5.8K | `docs/development/` | ⭐⭐ | Git 提交建議（臨時文檔） |

---

#### 3. **`docs/testing/` - 測試相關文檔**
> 用途：測試報告、驗證結果、測試案例

| 文檔 | 大小 | 移動路徑 | 優先級 | 原因 |
|------|------|---------|--------|------|
| `TEST_RESULTS_SUMMARY.md` | 9.4K | `docs/testing/` | ⭐⭐⭐⭐ | 測試結果總結 |
| `V1_V2_USER_VALIDATION_REPORT.md` | 11K | `docs/testing/` | ⭐⭐⭐⭐ | V1/V2 版本驗證報告 |
| `V2_FINAL_SUMMARY.md` | 8.5K | `docs/testing/` | ⭐⭐⭐⭐ | V2 最終總結 |
| `EXPERIMENT_POLLUTION_STATUS.md` | 5.9K | `docs/testing/` | ⭐⭐⭐ | 實驗污染狀態報告 |
| `AI_ANSWER_COMPARISON_REPORT.md` | 14K | `docs/testing/` | ⭐⭐⭐ | AI 回答比較報告 |

---

#### 4. **`docs/refactoring-reports/` - 重構報告**
> 用途：系統重構記錄、改進報告

| 文檔 | 大小 | 移動路徑 | 優先級 | 原因 |
|------|------|---------|--------|------|
| `SEARCH_VERSION_PARAMETER_REMOVAL.md` | 3.7K | `docs/refactoring-reports/` | ⭐⭐⭐ | 參數移除重構報告 |

---

### ❌ **建議刪除的臨時文檔**

| 文檔 | 原因 | 資訊價值 |
|------|------|---------|
| `GIT_COMMIT_SUGGESTION.md` | 臨時性質，提交完成後可刪除 | 低（已完成提交） |

---

## 🚀 執行計畫（分階段）

### 階段 1：創建目錄結構（如果不存在）
```bash
mkdir -p docs/debugging
mkdir -p docs/development
mkdir -p docs/testing
mkdir -p docs/refactoring-reports
```

### 階段 2：移動核心文檔（高優先級 ⭐⭐⭐⭐⭐）
```bash
# 除錯與分析文檔（核心）
mv SAME_QUERY_DIFFERENT_RESULTS_ROOT_CAUSE.md docs/debugging/
mv DIFY_AI_LAYER3_SELECTION_MECHANISM_ANALYSIS.md docs/debugging/
mv WHERE_IS_LAYER3_SELECTION.md docs/debugging/

# 開發規劃文檔
mv LAYER3_STABILITY_IMPROVEMENT_PLAN.md docs/development/
```

### 階段 3：移動次要文檔（高優先級 ⭐⭐⭐⭐）
```bash
# 除錯文檔
mv WEB_FAILURE_ROOT_CAUSE_ANALYSIS.md docs/debugging/
mv USER_HYPOTHESIS_ANALYSIS.md docs/debugging/
mv CONVERSATION_MEMORY_PARADOX_EXPLAINED.md docs/debugging/

# 測試報告
mv TEST_RESULTS_SUMMARY.md docs/testing/
mv V1_V2_USER_VALIDATION_REPORT.md docs/testing/
mv V2_FINAL_SUMMARY.md docs/testing/
```

### 階段 4：移動輔助文檔（中優先級 ⭐⭐⭐）
```bash
# 除錯文檔
mv MEMORY_INTERVAL_THEORY_CORRECTION.md docs/debugging/
mv TEST_VS_WEB_SAME_CONVERSATION_ID_PARADOX.md docs/debugging/
mv WEB_VS_TEST_API_SETTINGS_COMPARISON.md docs/debugging/

# 開發指南
mv KEYWORD_CLEANING_QUICK_REF.md docs/development/

# 測試報告
mv EXPERIMENT_POLLUTION_STATUS.md docs/testing/
mv AI_ANSWER_COMPARISON_REPORT.md docs/testing/

# 重構報告
mv SEARCH_VERSION_PARAMETER_REMOVAL.md docs/refactoring-reports/
```

### 階段 5：移動特定問題文檔（低優先級 ⭐⭐）
```bash
# 除錯文檔
mv WEB_NEW_CHAT_BUTTON_BEHAVIOR.md docs/debugging/
mv CUP_ISSUE_SUMMARY.md docs/debugging/
```

### 階段 6：刪除臨時文檔（可選）
```bash
# 如果已完成提交，可刪除
rm GIT_COMMIT_SUGGESTION.md
```

---

## 📋 完整執行腳本

```bash
#!/bin/bash
# Document cleanup script
# 文檔清理腳本

cd /home/user/codes/ai-platform-web

echo "📁 創建目錄結構..."
mkdir -p docs/debugging
mkdir -p docs/development
mkdir -p docs/testing
mkdir -p docs/refactoring-reports

echo ""
echo "🔥 階段 1：移動核心文檔（⭐⭐⭐⭐⭐）"
mv -v SAME_QUERY_DIFFERENT_RESULTS_ROOT_CAUSE.md docs/debugging/
mv -v DIFY_AI_LAYER3_SELECTION_MECHANISM_ANALYSIS.md docs/debugging/
mv -v WHERE_IS_LAYER3_SELECTION.md docs/debugging/
mv -v LAYER3_STABILITY_IMPROVEMENT_PLAN.md docs/development/

echo ""
echo "⚡ 階段 2：移動高優先級文檔（⭐⭐⭐⭐）"
mv -v WEB_FAILURE_ROOT_CAUSE_ANALYSIS.md docs/debugging/
mv -v USER_HYPOTHESIS_ANALYSIS.md docs/debugging/
mv -v CONVERSATION_MEMORY_PARADOX_EXPLAINED.md docs/debugging/
mv -v TEST_RESULTS_SUMMARY.md docs/testing/
mv -v V1_V2_USER_VALIDATION_REPORT.md docs/testing/
mv -v V2_FINAL_SUMMARY.md docs/testing/

echo ""
echo "📊 階段 3：移動中優先級文檔（⭐⭐⭐）"
mv -v MEMORY_INTERVAL_THEORY_CORRECTION.md docs/debugging/
mv -v TEST_VS_WEB_SAME_CONVERSATION_ID_PARADOX.md docs/debugging/
mv -v WEB_VS_TEST_API_SETTINGS_COMPARISON.md docs/debugging/
mv -v KEYWORD_CLEANING_QUICK_REF.md docs/development/
mv -v EXPERIMENT_POLLUTION_STATUS.md docs/testing/
mv -v AI_ANSWER_COMPARISON_REPORT.md docs/testing/
mv -v SEARCH_VERSION_PARAMETER_REMOVAL.md docs/refactoring-reports/

echo ""
echo "🔧 階段 4：移動特定問題文檔（⭐⭐）"
mv -v WEB_NEW_CHAT_BUTTON_BEHAVIOR.md docs/debugging/
mv -v CUP_ISSUE_SUMMARY.md docs/debugging/

echo ""
echo "✅ 文檔整理完成！"
echo ""
echo "📂 整理後的目錄結構："
echo "   docs/debugging/        - 11 個除錯文檔"
echo "   docs/development/      - 2 個開發指南"
echo "   docs/testing/          - 5 個測試報告"
echo "   docs/refactoring-reports/ - 1 個重構報告"
echo ""
echo "💡 建議：執行 'ls -lh docs/*/' 檢查結果"
```

---

## 📚 移動後的目錄結構預覽

```
docs/
├── debugging/ (11 個文檔)
│   ├── SAME_QUERY_DIFFERENT_RESULTS_ROOT_CAUSE.md ⭐⭐⭐⭐⭐
│   ├── DIFY_AI_LAYER3_SELECTION_MECHANISM_ANALYSIS.md ⭐⭐⭐⭐⭐
│   ├── WHERE_IS_LAYER3_SELECTION.md ⭐⭐⭐⭐⭐
│   ├── WEB_FAILURE_ROOT_CAUSE_ANALYSIS.md ⭐⭐⭐⭐
│   ├── USER_HYPOTHESIS_ANALYSIS.md ⭐⭐⭐⭐
│   ├── CONVERSATION_MEMORY_PARADOX_EXPLAINED.md ⭐⭐⭐⭐
│   ├── MEMORY_INTERVAL_THEORY_CORRECTION.md ⭐⭐⭐
│   ├── TEST_VS_WEB_SAME_CONVERSATION_ID_PARADOX.md ⭐⭐⭐
│   ├── WEB_VS_TEST_API_SETTINGS_COMPARISON.md ⭐⭐⭐
│   ├── WEB_NEW_CHAT_BUTTON_BEHAVIOR.md ⭐⭐
│   └── CUP_ISSUE_SUMMARY.md ⭐⭐
│
├── development/ (2 個文檔)
│   ├── LAYER3_STABILITY_IMPROVEMENT_PLAN.md ⭐⭐⭐⭐⭐
│   └── KEYWORD_CLEANING_QUICK_REF.md ⭐⭐⭐
│
├── testing/ (5 個文檔)
│   ├── TEST_RESULTS_SUMMARY.md ⭐⭐⭐⭐
│   ├── V1_V2_USER_VALIDATION_REPORT.md ⭐⭐⭐⭐
│   ├── V2_FINAL_SUMMARY.md ⭐⭐⭐⭐
│   ├── EXPERIMENT_POLLUTION_STATUS.md ⭐⭐⭐
│   └── AI_ANSWER_COMPARISON_REPORT.md ⭐⭐⭐
│
└── refactoring-reports/ (1 個文檔)
    └── SEARCH_VERSION_PARAMETER_REMOVAL.md ⭐⭐⭐
```

---

## 🎯 重點文檔索引（移動後）

### 📖 必讀核心文檔（⭐⭐⭐⭐⭐）

1. **`docs/debugging/DIFY_AI_LAYER3_SELECTION_MECHANISM_ANALYSIS.md`** (30K)
   - 用途：完整的 Layer 3 機制分析
   - 內容：5 大機制、數學模型、實驗數據分析
   - 適用：深入理解 Dify AI 智能選擇邏輯

2. **`docs/debugging/WHERE_IS_LAYER3_SELECTION.md`** (22K)
   - 用途：解答「Layer 3 程式碼在哪裡」
   - 內容：完整架構圖、代碼流程、黑箱解釋
   - 適用：理解系統架構和 Dify 整合

3. **`docs/development/LAYER3_STABILITY_IMPROVEMENT_PLAN.md`** (26K)
   - 用途：穩定度提升完整方案
   - 內容：4 大類 7 個方案、實施步驟、預期效果
   - 適用：執行改進和優化

4. **`docs/debugging/SAME_QUERY_DIFFERENT_RESULTS_ROOT_CAUSE.md`** (12K)
   - 用途：根本原因分析
   - 內容：問題現象、向量搜尋驗證、Dify 機制解釋
   - 適用：問題排查和用戶解釋

---

## ⚠️ 注意事項

### 移動前確認
- [ ] 確認沒有其他程式碼或腳本引用這些文檔
- [ ] 備份重要文檔（如果需要）
- [ ] 檢查是否有未提交的修改

### 移動後更新
- [ ] 更新 `docs/README.md` 添加新文檔索引
- [ ] 更新相關文檔中的內部連結（如有交叉引用）
- [ ] 通知團隊成員文檔位置變更

### Git 操作建議
```bash
# 使用 git mv 保留歷史記錄
git mv SAME_QUERY_DIFFERENT_RESULTS_ROOT_CAUSE.md docs/debugging/
git mv DIFY_AI_LAYER3_SELECTION_MECHANISM_ANALYSIS.md docs/debugging/
# ... 其他文檔

# 提交
git add .
git commit -m "docs: reorganize root-level documents into docs/ subdirectories

- Move 11 debugging documents to docs/debugging/
- Move 2 development guides to docs/development/
- Move 5 testing reports to docs/testing/
- Move 1 refactoring report to docs/refactoring-reports/

This improves documentation organization and follows the 8-category 
documentation structure defined in docs/ai_instructions.md"
```

---

## 📅 文檔資訊

- **創建日期**: 2025-11-12
- **版本**: v1.0
- **用途**: 文檔清理與重新組織計畫
- **狀態**: ✅ 計畫完成，待執行

---

**💡 建議：先執行核心文檔（階段 1-2），確認沒問題後再執行其他階段。**
