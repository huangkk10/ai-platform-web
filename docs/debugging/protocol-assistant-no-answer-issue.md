# Protocol Assistant AI 無法回答問題診斷指南

**問題症狀**：Dify 顯示「已找到引用來源」，但 AI 回答「不清楚」或「不確定」

**日期**：2025-11-10  
**相關截圖**：CrystalDiskMark 查詢案例（84% 相關度，仍回答不清楚）

---

## 🔍 問題分析

### 觀察到的現象
```
用戶查詢：「crystaldiskmark 全文」
引用來源：✅ CrystalDiskMark 5 (84%)
AI 回答：❌ 「很抱歉，我不清楚 CrystalDiskMark 的完整內容」
```

### 🎯 核心問題
**AI 已經收到知識庫資料，但選擇不使用它來回答問題。**

---

## 🔧 可能原因與解決方案

### 原因 1️⃣：Dify 工作室的 Score 閾值設定過高

#### 問題說明
Dify 工作室中設定了過高的相似度閾值（如 0.85 或 0.9），導致：
- Django 外部 API 返回的 0.84 分數被認為「不夠高」
- Dify 過濾掉這些結果
- AI 認為「沒有足夠資料」

#### 診斷方法
```bash
# 檢查當前 Dify 配置（代碼中的設定）
grep -A 10 "retrieval_model" library/common/knowledge_base/base_api_handler.py
```

**預期結果**：
```python
'retrieval_model': {
    'search_method': 'semantic_search',
    'reranking_enable': False,
    'top_k': 3,
    'score_threshold_enabled': False,  # ✅ 應該是 False
}
```

#### 🔴 如果看到這些設定（錯誤）
```python
'score_threshold_enabled': True,
'score_threshold': 0.75  # 或 0.8, 0.85
```

#### ✅ 解決方案 1
**在 Django 端關閉 Dify 的二次過濾**（已實施）

檔案：`library/common/knowledge_base/base_api_handler.py`（第 281 行）

```python
'retrieval_model': {
    'search_method': 'semantic_search',
    'reranking_enable': False,
    'reranking_mode': None,
    'top_k': 3,
    'score_threshold_enabled': False,  # ✅ 關閉 Dify 端過濾
}
```

**原理**：
- Django 外部知識庫 API 已經使用 `threshold=0.7` 過濾
- Dify 端不需要再次過濾
- 避免雙重閾值導致資料被過度過濾

---

### 原因 2️⃣：Dify 工作室的提示詞（Prompt）過於保守

#### 問題說明
Dify 工作室的 System Prompt 中可能包含類似指令：
```
如果你不確定答案，請誠實地說「我不知道」。
不要根據不相關的資料進行猜測。
只有在非常確定時才回答問題。
```

#### 診斷方法
1. 登入 Dify 工作室：`http://10.10.172.37`
2. 進入 **Protocol Guide** 應用
3. 檢查 **編排 → 提示詞** 部分

#### 🔴 問題提示詞範例
```
你是一個專業的技術助手。

重要規則：
- 如果知識庫中的資料相關性低於 90%，請說「我不確定」
- 只有在完全確定時才提供答案
- 寧可說不知道，也不要提供可能錯誤的資訊
```

#### ✅ 解決方案 2A：調整提示詞（推薦）
```
你是一個專業的 Protocol 測試助手。

任務：
- 根據提供的知識庫資料回答用戶問題
- 如果資料完整，直接提供答案
- 如果資料部分相關，說明「根據現有資料...」
- 只有在完全沒有相關資料時才說「我不清楚」

回答風格：
- 清晰、專業、實用
- 優先使用知識庫資料
- 適當引用來源文檔
```

#### ✅ 解決方案 2B：移除過度保守的指令
刪除或修改以下類型的指令：
- ❌ 「如果不確定就說不知道」
- ❌ 「只有在完全確定時才回答」
- ❌ 「相關性低於 X% 就不要回答」

---

### 原因 3️⃣：知識庫資料格式問題

#### 問題說明
外部知識庫 API 返回的資料格式可能不符合 Dify 的預期：
- `title` 欄位為空
- `content` 欄位過短或過長
- `metadata` 缺少關鍵資訊

#### 診斷方法
```bash
# 測試外部知識庫 API
curl -X POST "http://localhost/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "protocol_guide_db",
    "query": "crystaldiskmark 全文",
    "retrieval_setting": {"top_k": 3, "score_threshold": 0.5}
  }' | python3 -m json.tool
```

#### 🔴 檢查返回格式
```json
{
  "records": [
    {
      "content": "...",
      "score": 0.84,
      "title": "",  // ❌ 標題為空
      "metadata": {}  // ❌ metadata 為空
    }
  ]
}
```

#### ✅ 解決方案 3：確保資料格式完整
檔案：`library/protocol_guide/search_service.py`（第 180-190 行）

```python
def _expand_to_full_document(self, section_result, sections):
    # ... 組裝邏輯
    
    return {
        'content': assembled_content,
        'score': section_result['score'],
        'title': document_title,  # ✅ 確保有標題
        'metadata': {
            'document_title': document_title,
            'sections_count': len(full_documents),
            'is_full_document': True,  # ✅ 標記為完整文檔
            'source_table': 'protocol_guide'
        }
    }
```

---

### 原因 4️⃣：Top K 設定過低

#### 問題說明
如果 `top_k` 設定為 1 或 2，可能最相關的結果沒有被返回。

#### 診斷方法
```bash
# 檢查當前 Top K 設定
grep -n "top_k" library/common/knowledge_base/base_api_handler.py
```

#### ✅ 解決方案 4
確保 `top_k` 至少為 3：

```python
'retrieval_model': {
    'top_k': 3,  # ✅ 至少 3 個結果
}
```

---

## 🧪 完整診斷流程

### 步驟 1：檢查 Django 外部 API
```bash
# 測試 API 是否返回資料
curl -X POST "http://localhost/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "protocol_guide_db",
    "query": "crystaldiskmark 全文",
    "retrieval_setting": {"top_k": 3, "score_threshold": 0.5}
  }' | python3 -m json.tool | grep -A 5 '"title"'
```

**預期**：應該看到 `"title": "CrystalDiskMark 5"`

### 步驟 2：檢查 Django 配置
```bash
# 確認 score_threshold_enabled = False
grep -A 5 "score_threshold_enabled" library/common/knowledge_base/base_api_handler.py
```

**預期**：
```python
'score_threshold_enabled': False,  # ✅
```

### 步驟 3：檢查 Dify 工作室設定
1. 登入 Dify：`http://10.10.172.37`
2. 進入 **Protocol Guide** 應用
3. 檢查 **知識庫設定**：
   - Score 閾值：應該 **停用** 或設為 **0.5**
   - Top K：應該為 **3** 或更多
4. 檢查 **提示詞**：
   - 移除過度保守的指令
   - 確保 AI 會使用提供的資料

### 步驟 4：查看 Django 日誌
```bash
# 查看最近的 Dify 請求日誌
docker logs ai-django | grep "Protocol" | tail -30
```

尋找：
- 是否成功發送請求到 Dify
- Dify 返回的 `retriever_resources` 是否包含資料
- 是否有錯誤訊息

### 步驟 5：測試不同查詢
```bash
# 測試 1：明確的 SOP 查詢（應該觸發文檔級搜尋）
curl -X POST "http://localhost/api/protocol-guide/chat/" \
  -H "Content-Type: application/json" \
  -d '{"message": "crystaldiskmark sop", "conversation_id": ""}'

# 測試 2：完整關鍵字
curl -X POST "http://localhost/api/protocol-guide/chat/" \
  -H "Content-Type: application/json" \
  -d '{"message": "請給我完整的 crystaldiskmark 說明", "conversation_id": ""}'
```

---

## 🎯 推薦解決方案（按優先順序）

### 🥇 優先 1：調整 Dify 工作室提示詞
**影響**：立即生效，不需要修改代碼

**操作步驟**：
1. 登入 Dify 工作室
2. 編輯 Protocol Guide 應用
3. 修改 System Prompt：
   ```
   你是專業的 Protocol 測試助手。
   
   請根據提供的知識庫資料回答用戶問題。
   如果資料完整，直接提供詳細答案。
   如果資料部分相關，說明「根據現有資料...」並給出答案。
   只有在完全沒有相關資料時才說「抱歉，我找不到相關資訊」。
   
   回答時請：
   - 使用清晰的格式
   - 引用具體的文檔來源
   - 提供實用的建議
   ```
4. 儲存並測試

### 🥈 優先 2：確認 Django 配置正確
**影響**：避免雙重過濾

**檢查檔案**：`library/common/knowledge_base/base_api_handler.py`

確認：
```python
'score_threshold_enabled': False,  # ✅ 必須是 False
```

如果不是，修改並重啟：
```bash
docker compose restart ai-django
```

### 🥉 優先 3：降低 Django 端的閾值（謹慎）
**影響**：可能返回更多低質量結果

**檔案**：`library/protocol_guide/search_service.py`

```python
def semantic_search(self, 
                    query: str,
                    limit: int = 5,
                    threshold: float = 0.5) -> list:  # ✅ 從 0.7 降到 0.5
```

**權衡**：
- ✅ 優點：更多結果被返回給 Dify
- ❌ 缺點：可能包含不太相關的資料

---

## 📊 成功案例對比

### ❌ 失敗案例（當前）
```
查詢：crystaldiskmark 全文
返回：CrystalDiskMark 5 (84%)
AI：「很抱歉，我不清楚...」
```

### ✅ 成功案例（預期）
```
查詢：crystaldiskmark 全文
返回：CrystalDiskMark 5 (84%)
AI：「根據知識庫資料，CrystalDiskMark 是一個磁碟效能測試工具...
     [詳細內容]
     
     引用來源：CrystalDiskMark 5」
```

---

## 🔄 驗證修復

### 測試腳本
```bash
#!/bin/bash
# 測試 Protocol Assistant 是否正確使用知識庫資料

echo "測試 1：CrystalDiskMark 查詢"
curl -s -X POST "http://localhost/api/protocol-guide/chat/" \
  -H "Content-Type: application/json" \
  -d '{"message": "crystaldiskmark 完整說明", "conversation_id": ""}' \
  | python3 -c "import sys, json; data=json.load(sys.stdin); print('✅ 成功' if 'CrystalDiskMark' in data.get('answer', '') else '❌ 失敗')"

echo "測試 2：SOP 查詢"
curl -s -X POST "http://localhost/api/protocol-guide/chat/" \
  -H "Content-Type: application/json" \
  -d '{"message": "crystaldiskmark sop", "conversation_id": ""}' \
  | python3 -c "import sys, json; data=json.load(sys.stdin); print('✅ 成功' if len(data.get('answer', '')) > 500 else '❌ 失敗')"
```

### 預期結果
```
測試 1：CrystalDiskMark 查詢
✅ 成功

測試 2：SOP 查詢
✅ 成功
```

---

## 📚 相關文檔

- **文檔級搜尋觸發條件**：`/docs/features/document-level-search-trigger-conditions.md`
- **Dify 配置使用指南**：`/docs/ai-integration/dify-app-config-usage.md`
- **故障排除指南**：`/docs/debugging/dify-knowledge-not-showing-issue.md`

---

**作者**：AI Platform Team  
**更新日期**：2025-11-10  
**版本**：v1.0  
**狀態**：待驗證
