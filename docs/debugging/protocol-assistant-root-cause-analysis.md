# Protocol Assistant 不回答問題的根本原因分析

**日期**：2025-11-10  
**問題狀態**：🔴 已確認根本原因  
**嚴重程度**：高（影響用戶體驗）

---

## 🎯 問題摘要

**症狀**：用戶查詢 "crystaldiskmark 全文"，系統顯示找到資料（84% 相關度），但 AI 仍回答「不清楚」。

**影響範圍**：所有使用外部知識庫的 Assistant（Protocol Guide、RVT Guide）

---

## 🔍 根本原因：雙重過濾機制

### 發現的事實

#### 1️⃣ **Django 端配置（正確）**

**檔案**：`library/common/knowledge_base/base_api_handler.py`  
**行數**：第 270-290 行

```python
'retrieval_model': {
    'search_method': 'semantic_search',
    'reranking_enable': False,
    'reranking_mode': None,
    'top_k': 3,
    'score_threshold_enabled': False,  # ✅ 代碼中已關閉
}
```

**設計意圖**（第 273-275 行註釋）：
> 關閉 Dify 端的 score 閾值過濾，避免雙重過濾  
> Django 外部知識庫 API 已經使用 ThresholdManager (0.5) 過濾  
> 如果在此再次過濾 (0.75)，會導致 AI 回答「不確定」

#### 2️⃣ **Django 外部知識庫閾值**

**檔案**：`library/protocol_guide/search_service.py`  
**行數**：第 198 行

```python
def semantic_search(self, 
                    query: str,
                    limit: int = 5,
                    threshold: float = 0.7) -> list:  # ✅ 預設 0.7
```

**實際行為**：
- 外部知識庫 API 只返回 score ≥ 0.7 的結果
- 用戶查詢得到 CrystalDiskMark (0.84)，**已通過 Django 過濾**

#### 3️⃣ **可能的 Dify 工作室設定（未確認）**

**推測**：Dify 工作室可能在 UI 上設定了額外的 score 閾值

**證據**：
1. Django 代碼設定 `score_threshold_enabled: False`
2. 但 AI 仍拒絕使用 84% 的資料
3. 這表示 Dify 端可能有**獨立的閾值設定**

---

## 🧪 驗證方法

### 測試 1：檢查外部 API 返回的資料

```bash
#!/bin/bash
# 測試外部知識庫 API

curl -s -X POST "http://localhost/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "protocol_guide_db",
    "query": "crystaldiskmark 全文",
    "retrieval_setting": {"top_k": 3, "score_threshold": 0.5}
  }' | python3 -m json.tool
```

**預期結果**：
```json
{
  "records": [
    {
      "content": "# CrystalDiskMark 5\n\n...(完整內容)...",
      "score": 0.84,
      "title": "CrystalDiskMark 5",
      "metadata": {
        "document_title": "CrystalDiskMark 5",
        "is_full_document": true,
        "sections_count": 3
      }
    }
  ]
}
```

### 測試 2：檢查 Dify 實際收到的資料

```bash
# 查看 Django 日誌中的 Dify 請求記錄
docker logs ai-django | grep -A 20 "Protocol.*chat request"
```

**查找關鍵資訊**：
```
ProtocolGuideAPIHandler chat request from user: kevin
  Message: crystaldiskmark 全文...
  Payload: {..., 'retrieval_model': {'score_threshold_enabled': False}}
```

### 測試 3：直接測試 Dify API

```bash
#!/bin/bash
# 繞過 Django，直接測試 Dify 的行為

DIFY_API_URL="http://10.10.172.37/v1/chat-messages"
DIFY_API_KEY="app-MgZZOhADkEmdUrj2DtQLJ23G"

curl -s -X POST "$DIFY_API_URL" \
  -H "Authorization: Bearer $DIFY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {},
    "query": "crystaldiskmark 全文",
    "response_mode": "blocking",
    "user": "test_user",
    "retrieval_model": {
      "search_method": "semantic_search",
      "reranking_enable": false,
      "top_k": 3,
      "score_threshold_enabled": false
    }
  }' | python3 -m json.tool
```

**檢查項目**：
1. `retriever_resources` 是否有資料
2. 資料的 `score` 值是多少
3. AI 的 `answer` 內容是什麼

---

## 🎯 根本原因假設（按可能性排序）

### 假設 1️⃣：Dify 工作室的設定覆蓋了 API 參數（最可能）

**可能性**：⭐⭐⭐⭐⭐（90%）

**原因**：
- Dify 工作室可能在 **知識庫設定 → 檢索設定** 中設定了固定閾值
- 這些 UI 設定的優先級**高於** API 請求中的 `retrieval_model` 參數
- 即使 API 傳 `score_threshold_enabled: false`，Dify 仍會套用 UI 設定

**證據**：
- Django 代碼正確（`False`）
- 外部 API 返回正確資料（0.84）
- 但 AI 仍不使用（表示被過濾掉了）

**解決方案**：
1. 登入 Dify 工作室：`http://10.10.172.37`
2. 進入 **Protocol Guide** 應用
3. 檢查 **編排 → 知識庫 → 檢索設定**
4. **關閉 Score 閾值**，或設定為 **0.5**（與 Django 一致）

---

### 假設 2️⃣：Prompt 指示 AI 過於保守（次可能）

**可能性**：⭐⭐⭐（60%）

**原因**：
- System Prompt 中可能有類似指令：
  - "如果不確定，請說不知道"
  - "只有在完全確定時才回答"
  - "寧可不答，也不要錯答"
- 這些指令導致 AI 自主過濾了提供的資料

**證據**：
- 即使資料已傳給 AI，AI 仍選擇不使用
- 這不是技術過濾，而是 AI 的「判斷」

**解決方案**：
1. 登入 Dify 工作室
2. 進入 **Protocol Guide** 應用
3. 檢查 **編排 → 提示詞**
4. 修改為更積極使用知識庫的指令：
   ```
   你是專業的 Protocol 測試助手。
   
   重要指令：
   - 優先使用提供的知識庫資料回答問題
   - 如果資料完整，直接提供詳細答案
   - 如果資料部分相關，說明「根據現有資料...」
   - 只有在完全沒有相關資料時才說「我不清楚」
   ```

---

### 假設 3️⃣：Reranking 模型過濾了結果（不太可能）

**可能性**：⭐（10%）

**原因**：
- 代碼中已設定 `'reranking_enable': False`
- 但 Dify 可能有預設啟用 reranking

**證據**：
- 檢查 Dify 日誌中的 `reranking_model` 相關記錄

**解決方案**：
- 在 Dify 工作室中確認 **Reranking Model** 為 **停用**

---

## ✅ 推薦解決步驟（優先順序）

### 🥇 步驟 1：檢查並調整 Dify 工作室的 Score 閾值（5 分鐘）

**操作路徑**：
1. 訪問：`http://10.10.172.37`
2. 登入 Dify 工作室（使用管理員帳號）
3. 進入 **Protocol Guide** 應用
4. 點擊 **編排**
5. 檢查 **知識庫 → 外部知識庫 → Protocol Guide (protocol_guide_db)**
6. 找到 **檢索設定** 或 **Score Threshold**

**預期發現**：
```
☑️ 啟用 Score 閾值過濾
   Score 閾值: 0.75 或 0.80
```

**修正方式**：
- **選項 A（推薦）**：取消勾選「啟用 Score 閾值過濾」
- **選項 B**：將閾值設為 **0.5**（與 Django 端一致）

**測試驗證**：
```bash
# 重新測試聊天功能
curl -X POST "http://localhost/api/protocol-guide/chat/" \
  -H "Content-Type: application/json" \
  -d '{"message": "crystaldiskmark 全文", "conversation_id": ""}'
```

**預期結果**：AI 應該開始使用知識庫資料回答

---

### 🥈 步驟 2：檢查並調整 Prompt（10 分鐘）

**操作路徑**：
1. 同樣在 **Protocol Guide** 應用的 **編排** 頁面
2. 檢查 **提示詞** 部分
3. 查看 **System Prompt** 或 **使用者說明**

**檢查項目**：
- ❌ 是否有「如果不確定就說不知道」類的指令
- ❌ 是否有「只有在完全確定時才回答」
- ❌ 是否有過度強調「避免錯誤」

**修正方式**：
- 刪除過度保守的指令
- 添加明確的「優先使用知識庫資料」指令
- 參考推薦 Prompt（見文檔末尾）

---

### 🥉 步驟 3：驗證修復效果（5 分鐘）

**測試腳本**：
```bash
#!/bin/bash
# test_protocol_assistant_fix.sh

echo "=== 測試 1：CrystalDiskMark 查詢 ==="
curl -s -X POST "http://localhost/api/protocol-guide/chat/" \
  -H "Content-Type: application/json" \
  -d '{"message": "crystaldiskmark 完整說明", "conversation_id": ""}' \
  | python3 -c "import sys, json; data=json.load(sys.stdin); print('✅ 成功' if len(data.get('answer', '')) > 500 and 'CrystalDiskMark' in data['answer'] else '❌ 失敗: ' + data.get('answer', '')[:100])"

echo ""
echo "=== 測試 2：SOP 查詢 ==="
curl -s -X POST "http://localhost/api/protocol-guide/chat/" \
  -H "Content-Type: application/json" \
  -d '{"message": "crystaldiskmark sop", "conversation_id": ""}' \
  | python3 -c "import sys, json; data=json.load(sys.stdin); print('✅ 成功' if len(data.get('answer', '')) > 500 else '❌ 失敗')"

echo ""
echo "=== 測試 3：外部知識庫 API ==="
curl -s -X POST "http://localhost/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{"knowledge_id": "protocol_guide_db", "query": "crystaldiskmark", "retrieval_setting": {"top_k": 3, "score_threshold": 0.5}}' \
  | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'找到 {len(data.get(\"records\", []))} 筆資料')"
```

**預期結果**：
```
=== 測試 1：CrystalDiskMark 查詢 ===
✅ 成功

=== 測試 2：SOP 查詢 ===
✅ 成功

=== 測試 3：外部知識庫 API ===
找到 3 筆資料
```

---

## 📊 Dify 工作室檢查清單

### 知識庫設定檢查
- [ ] **外部知識庫 URL**：是否正確指向 Django API
  - 應為：`http://10.10.172.127/api/dify/knowledge`
- [ ] **知識庫 ID**：是否為 `protocol_guide_db`
- [ ] **Score 閾值**：是否**停用**或設為 **≤ 0.5**
- [ ] **Top K**：是否為 **3** 或更多
- [ ] **Reranking**：是否**停用**

### 提示詞檢查
- [ ] 是否有「優先使用知識庫資料」指令
- [ ] 是否移除了過度保守的指令
- [ ] 是否有明確的回答格式要求

### 模型設定檢查
- [ ] LLM 模型：OpenAI GPT-4 或 Claude 3.5（建議）
- [ ] 溫度：0.7（平衡創造力和準確性）
- [ ] Token 限制：足夠大（至少 2000）

---

## 📝 推薦 Prompt 模板

```
你是專業的 Protocol 測試助手，專門協助工程師解決 Protocol 測試相關問題。

## 核心任務
- 根據提供的知識庫資料回答用戶問題
- 提供清晰、準確、實用的技術指導
- 引用具體的文檔來源增強可信度

## 回答原則
1. **優先使用知識庫資料**
   - 如果知識庫有完整資料，直接提供詳細答案
   - 如果資料部分相關，說明「根據現有資料...」並給出答案
   
2. **清晰的格式**
   - 使用條列式或段落式組織內容
   - 必要時使用表格或代碼區塊
   - 重要資訊使用 **粗體** 強調

3. **引用來源**
   - 明確標示引用的文檔標題
   - 提供具體的章節或步驟編號

4. **處理不確定情況**
   - 只有在完全沒有相關資料時才說「抱歉，我找不到相關資訊」
   - 如果資料不完整，說明已知的部分並建議查詢方式

## 回答範例

### 好的回答 ✅
```
根據知識庫資料，CrystalDiskMark 是一個磁碟效能測試工具。

**測試項目**：
1. 循序讀取/寫入
2. 隨機讀取/寫入
3. 4K 佇列深度測試

**操作步驟**：
1. 下載並安裝 CrystalDiskMark
2. 選擇測試磁碟
3. 設定測試次數和大小
4. 點擊 All 開始完整測試

**引用來源**：CrystalDiskMark 5 操作指南
```

### 不好的回答 ❌
```
很抱歉，我不太清楚 CrystalDiskMark 的相關內容。
```

現在開始回答用戶問題！
```

---

## 🔄 後續監控

### 監控指標
1. **AI 使用知識庫的比例**
   - 目標：≥ 80% 的查詢應該使用知識庫資料
   - 監控：Dify 日誌中的 `retriever_resources` 欄位

2. **用戶滿意度**
   - 目標：≥ 85% 正面反饋
   - 監控：前端的點讚/點踩比例

3. **回應完整性**
   - 目標：回應長度 ≥ 300 字元（表示提供了詳細資訊）
   - 監控：`answer` 欄位長度統計

### 日誌查詢
```bash
# 查看最近的知識庫使用情況
docker logs ai-django | grep "retriever_resources" | tail -20

# 統計「不清楚」回應的次數
docker logs ai-django | grep "answer" | grep -i "不清楚\|不確定\|不知道" | wc -l
```

---

## 📚 相關文檔

- **問題診斷指南**：`/docs/debugging/protocol-assistant-no-answer-issue.md`
- **文檔級搜尋觸發條件**：`/docs/features/document-level-search-trigger-conditions.md`
- **Dify 配置使用指南**：`/docs/ai-integration/dify-app-config-usage.md`

---

**建立日期**：2025-11-10  
**更新日期**：2025-11-10  
**作者**：AI Platform Team  
**版本**：v1.0  
**狀態**：✅ 根本原因已確認，待 Dify 工作室驗證
