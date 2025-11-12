# 🔥 Web 前端 crystaldiskmark 查詢失敗根本原因分析

## 📊 問題總結

**用戶在 Web 上查詢 7 次，只有第 1 次成功（14.3%），後續 6 次全部失敗（85.7%）**

而測試腳本查詢 10 次，有 8 次成功（80%），只有 2 次失敗（20%）

## 🔍 關鍵證據：為什麼檢索到錯誤的 I3C 文檔？

### 證據 1：日誌顯示的檢索結果

**階段 1（原查詢 "crystaldiskmark"）**：
```
[INFO] 向量搜索返回 3 條結果 (threshold=0.85)
[INFO] 分數過濾: 3 -> 1 (threshold: 0.85)
[INFO] Python 二次過濾後: 1 條結果 (threshold=0.85)
[INFO] ✅ 搜索完成: 最終返回 1 條結果給 Dify
```

**問題**：3 個結果中，只有 **1 個通過 0.85 閾值**，但這 1 個是錯誤的！

---

**階段 2（改寫查詢 "crystaldiskmark 完整內容"）**：
```
[INFO] 📝 Stage 2 查詢重寫: crystaldiskmark → crystaldiskmark 完整內容
[INFO] 🎯 文檔級查詢檢測:
[INFO]    原始查詢: 'crystaldiskmark 完整內容'
[INFO]    檢測關鍵字: ['完整']
[INFO]    清理後查詢: 'crystaldiskmark 內容' (用於向量搜尋)

[INFO] 🔍 段落搜尋: query='crystaldiskmark 內容', source=protocol_guide, level=None-None, results=1, weights=95%/5%
[INFO] ✅ 段落向量搜尋成功: 1 個結果 (threshold=0.85)
[INFO] 🔄 將 1 個 section 結果擴展為完整文檔
[INFO] 📄 擴展為完整文檔，涉及 1 個文檔 (來自 1 個 source_ids)
[INFO] ✅ 組裝完成: I3C 相關說明, 包含 22 個 sections, 3623 字元  ← ❌ 錯誤文檔！
```

**關鍵問題**：階段 2 檢索到的 1 個 section 來自 **I3C 相關說明**，而不是 CrystalDiskMark！

---

## 🎯 根本原因分析

### 原因 1：向量搜尋結果的 Score 分佈問題

根據我的測試報告（`TEST_RESULTS_SUMMARY.md`），我發現：

```
成功案例引用來源：CrystalDiskMark 5 (90.74%)  ← 正確文檔
失敗案例引用來源：I3C 相關說明 (85.32%)     ← 錯誤文檔

Score 差距：90.74% - 85.32% = 5.42%
當前閾值：0.85 (85%)
```

**問題所在**：
1. ✅ CrystalDiskMark 5 的 score = 90.74% → 通過 0.85 閾值
2. ✅ I3C 相關說明的 score = 85.32% → **也通過 0.85 閾值**！
3. ⚠️ **當兩者都通過閾值時，向量搜尋的排名結果不穩定**

### 原因 2：查詢詞過短，語義不夠明確

**用戶查詢**：`crystaldiskmark`（單一關鍵字，14 字元）

**問題**：
- 查詢太短，缺乏語義上下文
- 向量模型難以準確判斷用戶意圖
- 多個文檔都可能與 "crystaldiskmark" 相關（I3C 文檔可能提到過 crystaldiskmark）

### 原因 3：階段 2 查詢改寫反而降低準確度

**當前邏輯**：
```python
# Stage 2 查詢重寫
stage_2_query = f"{original_query} 完整內容"

# 實際執行
"crystaldiskmark" → "crystaldiskmark 完整內容"

# 關鍵字清理後
"crystaldiskmark 完整內容" → "crystaldiskmark 內容"
```

**問題**：
1. 添加「完整內容」後，會觸發關鍵字清理機制
2. 清理後變成「crystaldiskmark 內容」
3. **「內容」這個詞過於通用**，反而干擾向量搜尋
4. 可能導致檢索到其他包含「內容」的文檔（如 I3C）

### 原因 4：段落搜尋權重配置可能不合適

```python
# 當前權重配置
標題權重: 95%
內容權重: 5%
```

**潛在問題**：
- 如果 I3C 文檔的某個 **section 標題** 包含 "crystaldiskmark" 或相似詞彙
- 由於標題權重高達 95%，可能優先匹配到 I3C
- 即使 CrystalDiskMark 文檔的整體相關性更高

### 原因 5：連續查詢的對話上下文干擾

從日誌看到，所有失敗案例都使用同一個 `conversation_id`：
```
Conversation ID: 4f5510ae-8df5-452e-903f-87aa6ca691b2
```

**可能的干擾**：
1. **Dify 的對話記憶機制**：前一次錯誤的回答（I3C）可能影響後續查詢
2. **向量搜尋的上下文偏移**：連續的錯誤可能形成「錯誤鏈」
3. **AI 模型的「記憶污染」**：Dify AI 可能記住了「這個用戶問 crystaldiskmark 時我回答了 I3C」

---

## 💡 為什麼測試腳本的成功率更高？

### 測試腳本的優勢

1. **新鮮的對話環境**
   - 測試腳本每次啟動時，Dify 對話上下文是乾淨的
   - 沒有前面錯誤回答的「記憶污染」

2. **時間間隔**
   - 測試腳本在查詢之間有 1 秒延遲
   - 給系統時間重置狀態

3. **隨機性**
   - 向量搜尋本身有一定隨機性（特別是 score 接近時）
   - 測試腳本運行時，資料庫狀態可能更穩定

### Web 前端的劣勢

1. **持續的對話上下文**
   - 用戶連續 7 次查詢都使用同一個 conversation_id
   - 第 1 次失敗後，後續 6 次都受到影響

2. **錯誤的累積效應**
   ```
   第 1 次：CrystalDiskMark 5 (90.74%) ✅ 成功
   第 2 次：I3C (85.32%) ❌ 失敗
   第 3-7 次：I3C (85.32%) ❌❌❌❌❌ 持續失敗
   ```
   → **一旦進入錯誤狀態，很難自動恢復**

3. **用戶行為模式**
   - 用戶看到錯誤回答後，可能快速連續重試
   - 沒有給系統足夠的「冷卻時間」

---

## 🔍 深入分析：I3C 文檔為什麼會被檢索到？

### 假設 1：I3C 文檔提到了 CrystalDiskMark

可能情況：
```markdown
# I3C 相關說明

## 測試工具
- 使用 CrystalDiskMark 進行硬碟效能測試
- 使用 I3C 協議進行資料傳輸測試
```

如果 I3C 文檔中提到 "CrystalDiskMark"：
- 向量搜尋會找到這個 section
- Score 可能達到 85.32%（剛好通過閾值）
- 但這不是專門的 CrystalDiskMark 文檔

### 假設 2：向量空間中的語義相似性

```
CrystalDiskMark：硬碟效能測試工具
I3C：高速資料傳輸協議

共同點：都與「效能」、「測試」、「速度」相關
```

向量模型可能認為兩者在語義空間中接近，特別是當：
- 查詢詞過短（"crystaldiskmark"）
- 缺乏明確的上下文（「我想知道如何使用 CrystalDiskMark 測試硬碟」）

### 假設 3：標題匹配優先於內容匹配

```python
# 權重配置
標題權重: 95%
內容權重: 5%
```

如果 I3C 文檔有一個 section 標題包含 "crystaldiskmark"：
```markdown
## CrystalDiskMark 測試結果比較
```

則這個 section 會因為**標題完全匹配**而獲得極高的 score。

---

## 🎯 為什麼第 1 次成功，後續 6 次失敗？

### 第 1 次成功的原因
1. **對話上下文乾淨**：新對話，無歷史干擾
2. **向量搜尋隨機性**：恰好排名正確（CrystalDiskMark 優先）
3. **Dify AI 狀態良好**：無記憶污染

### 第 2-7 次失敗的原因

**錯誤鏈條形成**：
```
第 2 次查詢:
  → Dify 記憶: "上次用戶問 crystaldiskmark，我回答了 CrystalDiskMark"
  → 向量搜尋: I3C (85.32%) 剛好通過閾值
  → Dify AI: "咦，這次檢索到 I3C？我不確定...回答'抱歉'"
  → 用戶收到: "抱歉，我目前沒有相關資訊" + I3C (85.32%)

第 3 次查詢:
  → Dify 記憶: "上次用戶問 crystaldiskmark，我說抱歉，並引用了 I3C"
  → 向量搜尋: 再次檢索到 I3C（因為記憶偏向）
  → Dify AI: "我還是不確定...再次回答'抱歉'"
  → 用戶收到: "抱歉..." + I3C

第 4-7 次:
  → 錯誤鏈條持續...
```

**關鍵機制**：
1. **Dify 對話記憶**：會記住歷史回答和引用的文檔
2. **向量搜尋偏向**：連續檢索到同一個文檔（I3C）
3. **不確定性檢測**：AI 持續回答「抱歉」
4. **無法自動恢復**：除非用戶清除對話或換個問法

---

## 📊 數據對比：測試 vs Web

| 指標 | 測試腳本（模式 1） | Web 前端（用戶實際） | 差異 |
|------|-------------------|---------------------|------|
| **成功率** | 80% (8/10) | 14.3% (1/7) | ❌ **相差 65.7%** |
| **失敗率** | 20% (2/10) | 85.7% (6/7) | ❌ **相差 65.7%** |
| **錯誤文檔** | I3C (85.32%) | I3C (85.32%) | ✅ 相同 |
| **連續失敗** | 最多 2 次 | 連續 6 次 | ❌ **更嚴重** |
| **自我恢復** | ✅ 有（測試 #9-10） | ❌ 無 | ❌ **無法恢復** |
| **對話上下文** | 新啟動測試 | 持續使用同一 conversation_id | ⚠️ **關鍵差異** |

---

## 🔥 關鍵結論

### 主要原因排序

1. **🥇 Score 閾值過低（0.85）** - **最重要**
   - 允許錯誤文檔（I3C 85.32%）通過
   - Score 差距太小（5.42%），無法有效區分
   
2. **🥈 對話記憶污染** - **Web 特有問題**
   - Dify 記住錯誤的回答和引用
   - 形成「錯誤鏈」，持續返回 I3C
   
3. **🥉 查詢詞過短** - **語義不明確**
   - "crystaldiskmark" 單一關鍵字
   - 缺乏上下文，難以準確匹配
   
4. **階段 2 查詢改寫問題**
   - "完整內容" 被清理成 "內容"
   - 反而降低查詢準確度
   
5. **段落搜尋權重配置**
   - 標題權重 95% 過高
   - 可能誤匹配 I3C 標題中的 "crystaldiskmark"

---

## 💡 解決方案（優先級排序）

### 🔥 立即執行（最高優先級）

#### 方案 1：提高 Score 閾值到 0.88

```python
# 修改前
score_threshold = 0.85  # 85%

# 修改後
score_threshold = 0.88  # 88%

# 效果:
# - I3C 相關說明 (85.32%) → ❌ 被過濾（低於閾值）
# - CrystalDiskMark 5 (90.74%) → ✅ 保留（高於閾值）
# 預期降級率: 85.7% → <10%
```

**實施步驟**：
```bash
# 1. 更新資料庫閾值設定
docker exec postgres_db psql -U postgres -d ai_platform -c "
UPDATE search_threshold_settings 
SET threshold = 0.88 
WHERE assistant_type = 'protocol_assistant';
"

# 2. 重新整理 ThresholdManager 快取
docker exec ai-django python manage.py shell -c "
from library.common.threshold_manager import ThresholdManager
ThresholdManager()._refresh_cache()
print('✅ 快取已重新整理')
"

# 3. 測試驗證
# 在 Web 上重新查詢 "crystaldiskmark"
```

---

#### 方案 2：添加「清除對話」功能提示

**前端改進**：
```javascript
// frontend/src/components/chat/CommonAssistantChatPage.jsx

// 在訊息列表上方添加提示
{messages.length > 3 && hasRepeatedFailures && (
  <Alert 
    message="建議清除對話" 
    description="如果多次查詢都無法獲得正確答案，請嘗試清除對話記錄後重新提問。"
    type="warning"
    action={
      <Button size="small" onClick={handleClearConversation}>
        清除對話
      </Button>
    }
    closable
  />
)}
```

**檢測重複失敗**：
```javascript
const hasRepeatedFailures = useMemo(() => {
  const lastThree = messages.slice(-3);
  return lastThree.filter(m => 
    m.type === 'assistant' && 
    m.content.includes('抱歉') && 
    m.content.length < 100
  ).length >= 2;
}, [messages]);
```

---

### 📊 短期優化（高優先級）

#### 方案 3：改進階段 2 查詢改寫策略

```python
# library/protocol_guide/two_tier_handler.py

def _request_dify_chat(self, query, conversation_id, user_id, is_full_search=False):
    """優化查詢改寫邏輯"""
    
    if is_full_search:
        # ❌ 舊邏輯：添加通用詞彙
        # rewritten_query = f"{query} 完整內容"
        
        # ✅ 新邏輯：添加更具體的上下文
        rewritten_query = f"請提供 {query} 測試工具的完整使用說明、安裝步驟和常見問題"
        
        logger.info(f"   📝 Stage 2 查詢優化: {query} → {rewritten_query}")
    else:
        rewritten_query = query
    
    # ... 其他代碼
```

**效果**：
- 原本：`crystaldiskmark 完整內容` → 清理後 `crystaldiskmark 內容`
- 改進：`請提供 crystaldiskmark 測試工具的完整使用說明...`
- 增加語義明確度，減少誤匹配

---

#### 方案 4：調整段落搜尋權重

```python
# library/common/knowledge_base/section_search_service.py

# 修改前
WEIGHT_CONFIGS = {
    'protocol_assistant': {
        'title_weight': 0.95,   # 95%
        'content_weight': 0.05  # 5%
    }
}

# 修改後
WEIGHT_CONFIGS = {
    'protocol_assistant': {
        'title_weight': 0.80,   # 80% ← 降低標題權重
        'content_weight': 0.20  # 20% ← 提高內容權重
    }
}
```

**理由**：
- 當前 95% 標題權重過於極端
- 可能導致標題匹配優先於整體內容相關性
- 調整為 80/20 更平衡

---

### 🔧 中期改進（中優先級）

#### 方案 5：添加文檔名稱驗證

```python
# library/protocol_guide/two_tier_handler.py

def _validate_document_relevance(self, query: str, document_name: str) -> bool:
    """驗證檢索到的文檔是否與查詢相關"""
    
    query_lower = query.lower()
    doc_lower = document_name.lower()
    
    # 提取查詢中的關鍵名詞
    key_terms = ['crystaldiskmark', 'unh', 'iol', 'i3c', 'usb', 'pcie']
    
    for term in key_terms:
        if term in query_lower:
            # 如果查詢包含特定術語，文檔名稱也應該包含
            if term not in doc_lower:
                logger.warning(f"⚠️ 文檔名稱不匹配: query含'{term}', document='{document_name}'")
                return False
    
    return True

# 在 Stage 2 使用
stage_2_response = self._request_dify_chat(...)
metadata = stage_2_response.get('metadata', {})
retriever_resources = metadata.get('retriever_resources', [])

for resource in retriever_resources:
    doc_name = resource.get('document_name', '')
    if not self._validate_document_relevance(user_query, doc_name):
        logger.warning(f"🔄 文檔不相關，觸發重試或降級")
        # 返回友善提示而非錯誤文檔
```

---

#### 方案 6：實作「對話重置」機制

```python
# library/protocol_guide/two_tier_handler.py

def handle_two_tier_search(self, user_query, conversation_id, user_id, **kwargs):
    """添加智能對話重置"""
    
    # 檢測是否需要重置對話
    if self._should_reset_conversation(conversation_id, user_query):
        logger.info("🔄 檢測到重複失敗，自動重置對話上下文")
        conversation_id = ""  # 強制使用新對話 ID
    
    # ... 原有邏輯

def _should_reset_conversation(self, conversation_id: str, query: str) -> bool:
    """檢測是否應該重置對話"""
    
    # 從快取中獲取最近的查詢歷史（需要實作 Redis 快取）
    recent_queries = self._get_recent_queries(conversation_id, limit=3)
    
    # 如果連續 3 次相同或相似查詢
    if len(recent_queries) >= 3:
        similar_count = sum(1 for q in recent_queries if self._is_similar_query(query, q))
        if similar_count >= 2:
            return True
    
    return False
```

---

### 🚀 長期優化（低優先級）

#### 方案 7：優化向量模型或重新訓練

```python
# 考慮：
# 1. 使用更大的 embedding 模型（如 1536 維）
# 2. Fine-tune 模型（使用 Protocol Guide 資料）
# 3. 添加 domain-specific 的向量權重
```

#### 方案 8：實作智能查詢擴展

```python
def expand_query_intelligently(query: str) -> str:
    """智能擴展查詢"""
    
    # 使用 LLM 生成更明確的查詢
    # "crystaldiskmark" → "如何使用 CrystalDiskMark 5 測試硬碟效能"
    pass
```

---

## 🧪 驗證方案

### 測試步驟

1. **修改 threshold 到 0.88**
2. **在 Web 上測試 10 次 "crystaldiskmark" 查詢**
3. **記錄成功率和引用文檔**
4. **對比修改前後的效果**

### 預期結果

| 指標 | 修改前 | 預期修改後 | 改善 |
|------|--------|-----------|------|
| **成功率** | 14.3% (1/7) | **>90% (9/10)** | ✅ +75.7% |
| **失敗率** | 85.7% (6/7) | **<10% (1/10)** | ✅ -75.7% |
| **錯誤文檔次數** | 6/7 | **0/10** | ✅ 完全消除 |
| **連續失敗** | 6 次 | **0 次** | ✅ 消除錯誤鏈 |

---

## 📝 總結

### 根本原因

1. **Score 閾值 0.85 過低** → 錯誤文檔（I3C 85.32%）通過閾值
2. **對話記憶污染** → 一次失敗後持續失敗（錯誤鏈）
3. **查詢過短** → 語義不明確
4. **查詢改寫問題** → "完整內容" → "內容"（降低準確度）

### 立即行動

**🔥 必須立即執行（預期 1 小時內解決）**：
```bash
# 1. 提高 threshold 到 0.88
docker exec postgres_db psql -U postgres -d ai_platform -c "
UPDATE search_threshold_settings 
SET threshold = 0.88 
WHERE assistant_type = 'protocol_assistant';
SELECT * FROM search_threshold_settings WHERE assistant_type = 'protocol_assistant';
"

# 2. 重新整理快取
docker exec ai-django python manage.py shell -c "
from library.common.threshold_manager import ThresholdManager
ThresholdManager()._refresh_cache()
"

# 3. 在 Web 上測試驗證（詢問 10 次 "crystaldiskmark"）
```

**預期效果**：
- ✅ I3C (85.32%) 被過濾
- ✅ 只保留 CrystalDiskMark 5 (90.74%)
- ✅ 成功率從 14.3% → >90%
- ✅ 用戶滿意度顯著提升

---

**📅 報告生成時間**: 2025-11-12  
**👤 分析者**: AI Platform Team  
**🎯 優先級**: 🔥🔥🔥 緊急（影響用戶體驗）
