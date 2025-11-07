# Protocol Assistant 問題修復摘要

## 🎯 問題
用戶提問「crystaldiskmark 如何放測」時，雖然找到了 2 份相關文件（87% 和 84% 相似度），但 AI 回答「抱歉，我不確定」。

## 🔍 根本原因
**雙重 Threshold 過濾導致 Dify 無法正確使用搜尋結果**

系統有兩層過濾：
1. **第一層**：Django 外部知識庫 API（ThresholdManager: 0.5）✅
2. **第二層**：Dify Chat API 的 retrieval_model（score_threshold: 0.75）❌

流程：
```
Django 搜尋 → 過濾 (0.5) → 返回結果給 Dify
                                ↓
                    Dify 再次過濾 (0.75) ← 問題所在！
                                ↓
                    結果被標記為「低信心」
                                ↓
                    LLM 回答「不確定」
```

## ✅ 解決方案
**關閉 Dify Chat API 中的 score_threshold，避免雙重過濾**

### 修改檔案
`/library/common/knowledge_base/base_api_handler.py`（約 270 行）

### 修改內容
```python
# 修改前
'retrieval_model': {
    'search_method': 'semantic_search',
    'reranking_enable': False,
    'reranking_mode': None,
    'top_k': 3,
    'score_threshold_enabled': True,   # ❌ 啟用二次過濾
    'score_threshold': 0.75             # ❌ 硬編碼高閾值
}

# 修改後
'retrieval_model': {
    'search_method': 'semantic_search',
    'reranking_enable': False,
    'reranking_mode': None,
    'top_k': 3,
    'score_threshold_enabled': False,   # ✅ 關閉二次過濾
    # 移除 score_threshold
}
```

## 📊 影響範圍
- ✅ Protocol Assistant（主要影響）
- ✅ RVT Assistant（使用相同基礎類別）
- ✅ 所有使用 `BaseKnowledgeBaseAPIHandler` 的 Assistant

## 🚀 已完成的操作
1. ✅ 修改 `base_api_handler.py`
2. ✅ 重啟 Django 容器
3. ✅ 創建驗證腳本：`/tests/test_protocol_assistant_fix.sh`
4. ✅ 創建詳細分析報告：`/docs/debugging/protocol-assistant-search-issue-analysis.md`

## 🧪 測試驗證
請測試以下問題並確認 AI 不再回答「不確定」：

1. **crystaldiskmark 如何放測**
   - 預期：返回具體的測試步驟和圖片引用

2. **burn in test 如何放測**
   - 預期：返回安裝和啟動步驟

3. **protocol 測試流程**
   - 預期：返回相關的測試流程說明

### 驗證清單
- [ ] AI 沒有回答「不確定」
- [ ] 回答包含具體的測試步驟
- [ ] 引用來源（CrystalDiskMark、Burn in Test）正確顯示
- [ ] 圖片引用標籤顯示正確（如 [IMG:41]）

## 📈 預期效果
修改後，當搜尋到相關文檔（相似度 > 0.5）時：
- ✅ Dify 會使用所有返回的文檔
- ✅ LLM 能夠基於文檔內容生成答案
- ✅ 減少「不確定」的回答頻率
- ✅ 提高用戶滿意度

## 🔗 相關文檔
- 詳細分析報告：`/docs/debugging/protocol-assistant-search-issue-analysis.md`
- 基礎 API Handler：`/library/common/knowledge_base/base_api_handler.py`
- Threshold Manager：`/library/common/threshold_manager.py`

## 📅 時間軸
- **問題發現**：2025-11-05 下午 08:06
- **根因分析**：2025-11-05 下午 16:00
- **修復完成**：2025-11-05 下午 16:15
- **容器重啟**：2025-11-05 下午 16:20

---

**狀態**：✅ 修復完成，等待測試驗證  
**下一步**：請測試並反饋結果
