# Protocol Assistant 搜尋結果不回答問題分析報告

## 📋 問題描述

**現象**：用戶提問「crystaldiskmark 如何放測」時，Protocol Assistant 雖然找到了 2 份相關文件（CrystalDiskMark 5 和 Burn in Test，相似度 87% 和 84%），但 AI 回答「抱歉，我不確定。[內容可能會發生錯誤，請查核重要資訊。]」

**時間**：2025-11-05 下午 08:06

**用戶**：admin

---

## 🔍 根本原因分析

### 1. **Score Threshold 設定過高導致 Dify 無法使用搜尋結果**

#### 問題核心：雙重 Threshold 機制衝突

系統目前有 **兩層 Threshold 過濾**：

```
用戶提問
  ↓
【第一層】Django 外部知識庫 API (ThresholdManager: 0.5)
  → 搜尋並過濾，返回結果給 Dify
  ↓
【第二層】Dify Chat API 的 retrieval_model (Score Threshold: 0.75) ⚠️
  → Dify 再次過濾結果
  ↓
LLM 生成回答
```

#### 實際日誌證據：

```log
# Django 端搜尋成功（使用 0.5 閾值）
[INFO] library.common.threshold_manager.ThresholdManager: 
  📊 使用資料庫 threshold: 0.5 (assistant=protocol_assistant)

[INFO] library.dify_knowledge.DifyKnowledgeSearchHandler: 
  Protocol Guide 搜索結果: 1 條
  🎯 [Stage 11] Python 二次過濾後: 1 條結果 (threshold=0.5)
  ✅ 搜索完成: 最終返回 1 條結果給 Dify

# 但發送給 Dify 的請求中，又設定了 0.75 閾值！
[INFO] library.common.knowledge_base.base_api_handler: 
  Payload: {
    'query': 'burn in test 如何放測',
    'retrieval_model': {
      'search_method': 'semantic_search',
      'top_k': 3,
      'score_threshold_enabled': True,
      'score_threshold': 0.75  ⚠️ 第二層過濾！
    }
  }

# Dify 返回了答案，但可能因為分數被二次過濾，導致信心不足
[INFO] library.common.knowledge_base.base_api_handler: 
  Dify answer (885 chars): 
  **如何在系統上安裝並啟動 BurnIn Test Pro 進行測試？**
  （正確回答了內容）
```

---

### 2. **為什麼 AI 會說「不確定」？**

雖然從日誌看到 Dify 有返回正確答案（Burn in Test 的安裝步驟），但可能存在以下情況：

#### 可能原因 1：Dify 內部 RAG 機制的問題
- Django 返回的搜尋結果已經通過 0.5 閾值
- 但 Dify Chat API 的 `retrieval_model.score_threshold: 0.75` 會**再次過濾**
- 如果文檔的原始分數在 0.5-0.75 之間，可能被 Dify 標記為「低信心」
- LLM 看到「低信心」標記，傾向回答「不確定」

#### 可能原因 2：Dify Prompt 設定
- Dify 的系統 Prompt 可能包含類似指令：
  ```
  如果檢索到的文檔相關性不高，請回答「抱歉，我不確定」
  ```
- 當 RAG 分數低於某個內部閾值時，LLM 被指示回答不確定

#### 可能原因 3：不同問題的行為
- 附件中用戶問的可能是 **crystaldiskmark**（相似度 87%）
- 但日誌記錄的是 **burn in test**（實際回答了）
- crystaldiskmark 的問題可能真的沒有足夠的文檔內容

---

## 🐛 問題代碼定位

### 位置：`/library/common/knowledge_base/base_api_handler.py`

```python
def handle_chat_api(cls, request):
    # ... 省略 ...
    
    payload = {
        'inputs': {},
        'query': message,
        'response_mode': 'blocking',
        'user': f"{cls.get_source_table()}_user_{request.user.id}",
        # 🔧 問題所在：強制設定了 Score 閾值 0.75
        'retrieval_model': {
            'search_method': 'semantic_search',
            'reranking_enable': False,
            'reranking_mode': None,
            'top_k': 3,
            'score_threshold_enabled': True,
            'score_threshold': 0.75  # ⚠️ 硬編碼的高閾值
        }
    }
```

---

## 🔧 解決方案

### 方案 1：**移除 Chat API 中的 Score Threshold（推薦）✅**

既然我們已經在 Django 外部知識庫 API 中使用 ThresholdManager 進行了過濾（0.5），就不應該在 Chat API 中再次過濾。

#### 修改代碼：

```python
# library/common/knowledge_base/base_api_handler.py

def handle_chat_api(cls, request):
    # ... 省略 ...
    
    payload = {
        'inputs': {},
        'query': message,
        'response_mode': 'blocking',
        'user': f"{cls.get_source_table()}_user_{request.user.id}",
        # ✅ 移除 retrieval_model 配置，讓 Dify 使用 APP 內的設定
        # 或者將 score_threshold_enabled 設為 False
        'retrieval_model': {
            'search_method': 'semantic_search',
            'reranking_enable': False,
            'reranking_mode': None,
            'top_k': 3,
            'score_threshold_enabled': False,  # ✅ 關閉二次過濾
            # 移除 score_threshold
        }
    }
```

**優點**：
- 避免雙重過濾導致的問題
- 統一使用 ThresholdManager 的設定（0.5）
- Dify 會使用所有返回的文檔

**缺點**：
- 無

---

### 方案 2：**使用 ThresholdManager 的閾值**

讓 Chat API 使用與外部知識庫 API 相同的閾值。

```python
def handle_chat_api(cls, request):
    # 獲取 ThresholdManager 的閾值
    from library.common.threshold_manager import ThresholdManager
    
    assistant_type = cls.get_assistant_type()  # 需要新增此方法
    threshold = ThresholdManager.get_threshold(assistant_type)
    
    payload = {
        'inputs': {},
        'query': message,
        'response_mode': 'blocking',
        'user': f"{cls.get_source_table()}_user_{request.user.id}",
        'retrieval_model': {
            'search_method': 'semantic_search',
            'reranking_enable': False,
            'reranking_mode': None,
            'top_k': 3,
            'score_threshold_enabled': True,
            'score_threshold': threshold  # ✅ 使用統一的閾值
        }
    }
```

**優點**：
- 統一使用 ThresholdManager
- 可動態調整閾值

**缺點**：
- 需要額外實作 `get_assistant_type()` 方法
- 仍然有雙重過濾的風險

---

### 方案 3：**完全移除 retrieval_model 參數（最簡單）✅**

讓 Dify 完全使用應用內配置的 RAG 設定。

```python
payload = {
    'inputs': {},
    'query': message,
    'response_mode': 'blocking',
    'user': f"{cls.get_source_table()}_user_{request.user.id}",
    # ✅ 完全移除 retrieval_model，讓 Dify APP 自己決定
}

if conversation_id:
    payload['conversation_id'] = conversation_id
```

**優點**：
- 最簡單的解決方案
- Dify 使用 APP 內的 RAG 配置（可在 Dify 工作室調整）
- 避免硬編碼的問題

**缺點**：
- 無法在程式碼中動態控制 RAG 參數

---

## 📊 建議實施方案

### **推薦：方案 1（關閉 score_threshold_enabled）**

理由：
1. **保持控制權**：仍然可以在程式碼中設定 RAG 參數
2. **避免雙重過濾**：關閉 Dify 端的分數過濾
3. **統一閾值管理**：由 Django 的 ThresholdManager 統一管理
4. **最小改動**：只需修改一行代碼

### 實施步驟：

#### 1. 修改 `base_api_handler.py`

```python
# library/common/knowledge_base/base_api_handler.py (約 270 行)

'retrieval_model': {
    'search_method': 'semantic_search',
    'reranking_enable': False,
    'reranking_mode': None,
    'top_k': 3,
    'score_threshold_enabled': False,  # ✅ 改為 False
    # 移除或註解掉 score_threshold
}
```

#### 2. 測試驗證

```bash
# 1. 重啟 Django 容器
docker compose restart ai-django

# 2. 在 Protocol Assistant 提問測試
問題：「crystaldiskmark 如何放測」

# 3. 檢查日誌
docker logs ai-django --tail 50 | grep "Dify answer"

# 4. 確認 AI 是否正確回答
```

#### 3. 驗證清單

- [ ] AI 回答了具體內容（不是「不確定」）
- [ ] 引用來源正確顯示
- [ ] 回答內容與文檔相符
- [ ] 測試多個問題確保穩定性

---

## 🎯 預期效果

修改後：

```
用戶提問「crystaldiskmark 如何放測」
  ↓
Django 外部知識庫 API（ThresholdManager: 0.5）
  → 搜尋到 CrystalDiskMark 5 文檔（87% 相似度）✅
  → 返回給 Dify
  ↓
Dify Chat API（score_threshold_enabled: False）
  → 不進行二次過濾 ✅
  → 使用所有返回的文檔
  ↓
LLM 生成回答
  → 基於搜尋到的文檔內容回答 ✅
  → 提供具體的測試步驟和圖片引用 ✅
```

---

## 📝 相關問題追蹤

### 相關文檔
- `/docs/architecture/dify-rag-architecture.md`（如果存在）
- `/library/common/threshold_manager.py`
- `/library/common/knowledge_base/base_api_handler.py`

### 影響範圍
- Protocol Assistant（已確認問題）
- RVT Assistant（可能有相同問題）
- 所有使用 `BaseKnowledgeBaseAPIHandler` 的 Assistant

### 後續優化
1. **統一 RAG 配置管理**：建立統一的 RAG 參數配置系統
2. **閾值策略文檔化**：明確說明何時使用哪一層的閾值
3. **增加監控指標**：追蹤「不確定」回答的頻率

---

## 🚀 執行計劃

### 立即行動（優先級：高）
1. ✅ 修改 `base_api_handler.py` 中的 `score_threshold_enabled` 為 `False`
2. ✅ 重啟 Django 容器
3. ✅ 測試 Protocol Assistant 和 RVT Assistant

### 短期行動（1-2 天）
1. 監控修改後的效果
2. 收集用戶反饋
3. 調整 ThresholdManager 的閾值（如需要）

### 長期行動（1-2 週）
1. 建立統一的 RAG 配置管理系統
2. 編寫 RAG 參數調優指南
3. 增加自動化測試確保問答質量

---

**報告生成時間**：2025-11-05 16:00  
**分析者**：AI Platform Team  
**狀態**：等待實施

---

## 🔗 附錄

### A. Dify RAG 參數說明

| 參數 | 說明 | 預設值 | 建議值 |
|------|------|--------|--------|
| `search_method` | 搜尋方法 | `semantic_search` | `semantic_search` |
| `top_k` | 返回結果數量 | 3 | 3-5 |
| `score_threshold_enabled` | 是否啟用分數過濾 | `False` | **False**（避免雙重過濾）|
| `score_threshold` | 分數閾值 | 無 | 移除（由 ThresholdManager 管理）|
| `reranking_enable` | 是否啟用重排序 | `False` | `False`（當前未使用）|

### B. ThresholdManager 當前設定

```sql
SELECT assistant_type, score_threshold, vector_weight, keyword_weight 
FROM search_threshold_settings;

-- 結果：
-- protocol_assistant: 0.5
-- rvt_assistant: 0.5
```

### C. 測試案例

```python
# 測試案例 1：crystaldiskmark
問題：「crystaldiskmark 如何放測」
預期：返回具體的測試步驟和圖片

# 測試案例 2：burn in test
問題：「burn in test 如何放測」
預期：返回安裝和啟動步驟

# 測試案例 3：低相似度問題
問題：「如何煮飯」（不在知識庫中）
預期：回答「抱歉，我不確定」或「知識庫中沒有相關資訊」
```
