# Protocol Assistant Dify 配置問題分析

## 🔍 問題現象

**時間**：2025-11-05 10:20:54

**問題**：用戶提問「crystaldiskmark 如何放測」

**搜尋結果**：
- ✅ Django 外部知識庫 API 找到 2 條結果（threshold: 0.5）
- ✅ 成功返回給 Dify

**Dify 回應**：
```
抱歉，我目前無法找到「CrystalDiskMark」相關的資訊...
```

## 📊 日誌證據

### 1. 搜尋階段（✅ 正常）
```log
[INFO] library.common.knowledge_base.base_search_service: 
  向量搜索返回 2 條結果 (threshold=0.5)

[INFO] library.dify_knowledge.DifyKnowledgeSearchHandler: 
  Protocol Guide 搜索結果: 2 條
  📊 [Stage 10] 搜索返回 2 條原始結果
  分數過濾: 2 -> 2 (threshold: 0.5)
  🎯 [Stage 11] Python 二次過濾後: 2 條結果 (threshold=0.5)
  ✅ 搜索完成: 最終返回 2 條結果給 Dify
```

### 2. Chat API 階段（✅ 修復已生效）
```log
[INFO] library.common.knowledge_base.base_api_handler: 
  Payload: {
    'query': 'crystaldiskmark 如何放測',
    'retrieval_model': {
      'search_method': 'semantic_search',
      'top_k': 3,
      'score_threshold_enabled': False,  # ✅ 已關閉二次過濾
    }
  }
```

### 3. Dify 回應（❌ 問題所在）
```log
[INFO] library.common.knowledge_base.base_api_handler: 
  Dify answer (202 chars): 
  抱歉，我目前無法找到「CrystalDiskMark」相關的資訊...
```

## 🔍 根本原因分析

### 問題：Dify APP 配置的檢索設定覆蓋了我們的參數

雖然我們在 Chat API 中設定了 `score_threshold_enabled: False`，但 **Dify APP 內部可能有自己的 Score Threshold 設定**。

#### Dify 的 RAG 參數優先級：
```
1. APP 內建配置（在 Dify 工作室設定）- 優先級最高 ⚠️
2. API 請求的 retrieval_model 參數 - 優先級中
3. 外部知識庫返回的結果 - 優先級最低
```

### 可能的情況：

#### 情況 1：Dify APP 設定了 Score Threshold
- Dify 工作室中，Protocol Guide APP 可能設定了 **Score Threshold ≥ 0.7**
- 即使我們傳送 `score_threshold_enabled: False`，APP 配置仍會生效
- 結果：2 份文檔（87%, 84%）被轉換為 **0.87 和 0.84**，但可能低於 Dify APP 的閾值

#### 情況 2：Dify APP 的提示詞問題
- Dify APP 的 System Prompt 可能包含類似指令：
  ```
  如果檢索到的文檔相關性低於 0.9，請回答「無法找到相關資訊」
  ```

#### 情況 3：Dify 外部知識庫的分數格式問題
- 我們返回的分數格式：0.87（87%）
- Dify 期望的分數格式可能不同

## 🔧 解決方案

### 方案 1：檢查並修改 Dify APP 配置（推薦）✅

#### 步驟 1：登入 Dify 工作室
```
URL: http://10.10.172.37
找到：Protocol_Guide APP
```

#### 步驟 2：檢查「知識庫」配置
1. 點擊 APP 設定
2. 進入「知識庫」或「檢索設定」
3. 檢查以下項目：
   - **Score Threshold**：應該設為 **關閉** 或 **≤ 0.5**
   - **Top K**：建議 3-5
   - **檢索模式**：語義搜尋
   - **重排序**：關閉

#### 步驟 3：檢查「提示詞」配置
1. 進入「編排」頁面
2. 查看 System Prompt
3. 確認沒有類似以下的指令：
   ```
   ❌ 如果檢索到的文檔相關性不高，請回答「無法找到」
   ❌ 只使用高信心的文檔來回答
   ```
4. 建議的 Prompt：
   ```
   ✅ 請基於提供的知識庫內容回答用戶問題
   ✅ 如果知識庫中有相關信息，請詳細說明
   ```

---

### 方案 2：在 API 請求中明確設定更多參數

修改 `base_api_handler.py` 的 payload：

```python
payload = {
    'inputs': {},
    'query': message,
    'response_mode': 'blocking',
    'user': f"{cls.get_source_table()}_user_{request.user.id}",
    'retrieval_model': {
        'search_method': 'semantic_search',
        'reranking_enable': False,
        'reranking_mode': None,
        'top_k': 5,  # ✅ 增加到 5（原為 3）
        'score_threshold_enabled': False,
        # ✅ 新增：明確告訴 Dify 不要過濾
        'score_threshold': 0.0,  # 設為 0.0 而非完全移除
    },
    # ✅ 新增：files 參數（可選）
    'files': []
}
```

---

### 方案 3：提高外部知識庫返回的分數

如果 Dify 內部有固定的閾值（如 0.9），我們可以調整返回的分數：

```python
# library/dify_knowledge/search_handler.py

# 在返回結果前，提高分數
for record in records:
    # 將 0.87 提升到 0.95（保持相對順序）
    original_score = record.get('score', 0.5)
    boosted_score = min(0.95, original_score + 0.1)  # 加 0.1，最高 0.95
    record['score'] = boosted_score
```

⚠️ **注意**：這是臨時解決方案，不建議長期使用。

---

## 🧪 驗證步驟

### 步驟 1：檢查 Dify APP 配置
```bash
# 記錄當前配置
1. Score Threshold: ________
2. Top K: ________
3. 檢索模式: ________
4. System Prompt 是否包含過濾指令: ________
```

### 步驟 2：測試不同的問題
```
1. "crystaldiskmark 如何放測" - 相似度 87%
2. "burn in test 如何放測" - 相似度 84%
3. "測試流程" - 相似度可能較低
```

### 步驟 3：對比 RVT Assistant
```bash
# RVT Assistant 是否有相同問題？
# 如果 RVT 正常，對比兩個 APP 的配置差異
```

---

## 📊 臨時測試方案

### 直接測試 Dify API

```bash
# 測試 1：發送已知的搜尋結果給 Dify
curl -X POST "http://10.10.172.37/v1/chat-messages" \
  -H "Authorization: Bearer app-MgZZOhADkEmdUrj2DtQLJ23G" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "crystaldiskmark 如何放測",
    "inputs": {},
    "response_mode": "blocking",
    "user": "test_user",
    "retrieval_model": {
      "search_method": "semantic_search",
      "reranking_enable": false,
      "top_k": 5,
      "score_threshold_enabled": false,
      "score_threshold": 0.0
    }
  }'
```

### 測試 2：檢查外部知識庫 API 返回的分數

```bash
# 直接調用外部知識庫 API
curl -X POST "http://10.10.172.37/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "protocol_guide_db",
    "query": "crystaldiskmark 如何放測",
    "retrieval_setting": {
      "top_k": 5,
      "score_threshold": 0.5
    }
  }'

# 查看返回的 records 中的 score 值
```

---

## 🎯 建議行動

### 立即行動（優先級：高）
1. **登入 Dify 工作室** - 檢查 Protocol Guide APP 的配置
2. **關閉 Score Threshold** - 在 APP 設定中關閉或設為 0
3. **檢查 System Prompt** - 移除任何過濾相關的指令

### 短期行動（1-2 天）
1. **對比 RVT Assistant** - 檢查為什麼 RVT 可能正常
2. **測試不同閾值** - 嘗試不同的 Score Threshold 設定
3. **記錄 Dify 配置** - 建立標準化的 Dify APP 配置文檔

### 長期行動（1-2 週）
1. **統一 RAG 配置** - 建立所有 Assistant 的標準配置
2. **增加監控** - 追蹤 Dify 返回「無法找到」的頻率
3. **優化提示詞** - 改進 Dify APP 的 System Prompt

---

## 📝 相關資訊

### Dify APP 資訊
- **APP 名稱**：Protocol Guide
- **Workspace**：Protocol_Guide
- **API Key**：app-MgZZOhADkEmdUrj2DtQLJ23G
- **API URL**：http://10.10.172.37/v1/chat-messages

### 外部知識庫 API
- **Endpoint**：http://10.10.172.37/api/dify/knowledge/retrieval/
- **Knowledge ID**：protocol_guide_db
- **當前 Threshold**：0.5（ThresholdManager）

### 相關文檔
- Dify 配置管理：`/library/config/dify_config_manager.py`
- 外部知識庫 API：`/backend/api/views/dify_knowledge_views.py`
- Chat API Handler：`/library/common/knowledge_base/base_api_handler.py`

---

**報告時間**：2025-11-05 18:30  
**狀態**：等待檢查 Dify APP 配置  
**下一步**：登入 Dify 工作室檢查 Protocol Guide APP 設定
