# 方案 A-Enhanced 實作完成報告

## 📋 問題摘要

**問題**：二階段搜尋的 Stage 2 無法正確使用全文搜尋模式

**根本原因**：
- Backend 在 `two_tier_handler.py` 中設定了 `search_mode='document_only'`
- 但 Dify 調用外部知識庫 API 時，**不會**將 `inputs` 參數傳遞給我們的 API
- 導致 Stage 2 仍然使用預設的 `auto` 模式（段落搜尋）

---

## ✅ 解決方案：方案 A-Enhanced（特殊標記 + 自動清理）

### **核心概念**
使用特殊標記 `__FULL_SEARCH__` 作為 Stage 2 的信號：
1. Backend 在 Stage 2 查詢中添加標記
2. 外部知識庫 API 檢測標記並切換模式
3. 在向量搜尋前自動清理標記
4. 不污染實際搜尋內容

---

## 🔧 實作內容

### **1. 修改 two_tier_handler.py**

**檔案位置**：`/home/user/codes/ai-platform-web/library/protocol_guide/two_tier_handler.py`

**修改內容**（約第 125 行）：
```python
# === 階段 2：全文級搜尋 ===
logger.info(f"   ⚠️ 階段 1 回答不確定 (含關鍵字: {stage_1_keyword})")
logger.info(f"   🔄 進入階段 2: 發送「原查詢 + __FULL_SEARCH__」給 Dify（全文級搜尋）...")

# ✅ 方案 A-Enhanced：添加特殊標記觸發全文搜尋
# 注意：Dify 不會將 inputs 參數傳遞給外部知識庫 API
# 所以我們使用查詢字串中的特殊標記來觸發全文搜尋
# 外部知識庫 API 會檢測並移除此標記，不影響實際搜尋
stage_2_query = f"{user_query} __FULL_SEARCH__"
logger.info(f"   🏷️ Stage 2 查詢（含標記）: {stage_2_query}")

stage_2_response = self._request_dify_chat(
    query=stage_2_query,  # ← 使用含標記的查詢
    conversation_id=conversation_id,
    user_id=user_id,
    is_full_search=True  # Stage 2 = 全文搜尋
)
```

**新增日誌**：
- `🔄 進入階段 2: 發送「原查詢 + __FULL_SEARCH__」給 Dify（全文級搜尋）...`
- `🏷️ Stage 2 查詢（含標記）: {query} __FULL_SEARCH__`

---

### **2. 修改 dify_knowledge_views.py**

**檔案位置**：`/home/user/codes/ai-platform-web/backend/api/views/dify_knowledge_views.py`

**修改內容**（約第 309-326 行）：
```python
# 解析請求資料
data = json.loads(request.body) if request.body else {}
knowledge_id = data.get('knowledge_id', 'employee_database')
query = data.get('query', '')
retrieval_setting = data.get('retrieval_setting', {})

# 🔍 檢測特殊標記 __FULL_SEARCH__（二階段搜尋 Stage 2 標記）
search_mode = 'auto'  # 預設為 'auto'（段落搜尋）

if '__FULL_SEARCH__' in query:
    # 檢測到 Stage 2 標記
    search_mode = 'document_only'  # 切換為全文搜尋
    query = query.replace('__FULL_SEARCH__', '').strip()  # 清理標記
    logger.info(f"🎯 檢測到 Stage 2 標記，切換到全文搜尋模式")
    logger.info(f"🧹 清理後查詢: '{query}'")

# ✅ 也支援從 Dify inputs 接收 search_mode（如果 Dify 工作室有配置）
inputs = data.get('inputs', {})
if 'search_mode' in inputs and '__FULL_SEARCH__' not in data.get('query', ''):
    # 如果 inputs 中有 search_mode，且不是來自標記，則使用 inputs 的值
    search_mode = inputs.get('search_mode', search_mode)
```

**新增日誌**：
- `🎯 檢測到 Stage 2 標記，切換到全文搜尋模式`
- `🧹 清理後查詢: '{query}'`

---

### **3. 驗證 search_mode 傳遞路徑**

**確認已支援**：
```
dify_knowledge_views.py (檢測標記 → search_mode='document_only')
    ↓
DifyKnowledgeSearchHandler.search() (接收 search_mode)
    ↓
search_knowledge_by_type() (傳遞 search_mode)
    ↓
BaseSearchService.search_with_vectors() (執行 search_mode)
```

**所有層級都已支援 `search_mode` 參數** ✅

---

## 🧪 測試方法

### **方法 1：使用瀏覽器測試（推薦）**

1. 登入 Protocol Assistant Chat
2. 發送查詢：`cup顏色`
3. 等待 Stage 2 觸發（AI 回應不確定）
4. 檢查後端日誌

**預期日誌輸出**：
```
[INFO] library.protocol_guide.two_tier_handler: 🔄 進入階段 2: 發送「原查詢 + __FULL_SEARCH__」給 Dify（全文級搜尋）...
[INFO] library.protocol_guide.two_tier_handler: 🏷️ Stage 2 查詢（含標記）: cup顏色 __FULL_SEARCH__
[INFO] api.views.dify_knowledge_views: 🎯 檢測到 Stage 2 標記，切換到全文搜尋模式
[INFO] api.views.dify_knowledge_views: 🧹 清理後查詢: 'cup顏色'
[INFO] library.dify_knowledge: 執行搜索: type=protocol_guide, query='cup顏色', limit=3, threshold=0.85, mode='document_only'
[INFO] library.common.knowledge_base.base_search_service: 🎯 文檔搜索模式 (search_mode='document_only')
```

---

### **方法 2：使用測試腳本**

```bash
# 需要替換 YOUR_TOKEN_HERE 為實際的 Auth Token
./test_stage2_full_search.sh
```

---

### **方法 3：即時監控日誌**

```bash
# 終端 1：啟動日誌監控
docker logs ai-django --tail 0 --follow | grep -E "階段|Stage|FULL_SEARCH|檢測到|清理後|document_only"

# 終端 2 或瀏覽器：發送查詢
# 在 Protocol Assistant Chat 中輸入：cup顏色
```

---

## ✅ 驗證檢查清單

執行測試後，確認以下日誌訊息都出現：

- [ ] `🔄 進入階段 2: 發送「原查詢 + __FULL_SEARCH__」給 Dify（全文級搜尋）...`
- [ ] `🏷️ Stage 2 查詢（含標記）: cup顏色 __FULL_SEARCH__`
- [ ] `🎯 檢測到 Stage 2 標記，切換到全文搜尋模式`
- [ ] `🧹 清理後查詢: 'cup顏色'`
- [ ] `mode='document_only'`（在搜尋執行日誌中）
- [ ] `🎯 文檔搜索模式` 或 `📄 使用文檔向量搜尋`

**如果所有項目都出現，表示方案 A-Enhanced 成功運作** ✅

---

## 📊 預期效果

### **修正前（問題狀態）**
```
Stage 1: auto 模式（段落搜尋）→ 不確定
Stage 2: auto 模式（段落搜尋）← ❌ 錯誤！應該使用全文搜尋
```

### **修正後（正確狀態）**
```
Stage 1: auto 模式（段落搜尋）→ 不確定
Stage 2: document_only 模式（全文搜尋）← ✅ 正確！
```

---

## 🎯 優點與限制

### **優點**
- ✅ 不依賴 Dify 配置修改
- ✅ 實作簡單，容易理解
- ✅ 標記會被自動清理，不污染搜尋
- ✅ 使用不常見的標記 `__FULL_SEARCH__`，不會與正常查詢衝突
- ✅ 向後相容：仍支援 Dify inputs 的 `search_mode`

### **限制**
- ⚠️ 屬於 workaround 方案（但在 Dify 限制下是合理的）
- ⚠️ 依賴查詢字串傳遞狀態（但已在清理前完成識別）

---

## 🔄 替代方案

如果未來 Dify 支援外部知識庫 API 接收 inputs 參數，可以直接使用：

**方案 C：修改 Dify 工作室配置**
1. 在 Dify 工作室的 Protocol Guide App 中添加 `search_mode` 輸入變數
2. 配置外部知識庫節點接收 `search_mode` 參數
3. Backend 通過 `inputs` 傳遞，Dify 轉發給外部知識庫 API
4. 移除 `__FULL_SEARCH__` 標記邏輯

---

## 📝 相關檔案

### **已修改檔案**
- `library/protocol_guide/two_tier_handler.py` - 添加 `__FULL_SEARCH__` 標記
- `backend/api/views/dify_knowledge_views.py` - 檢測並清理標記

### **已驗證檔案（無需修改）**
- `library/dify_knowledge/__init__.py` - 已支援 `search_mode` 參數
- `library/common/knowledge_base/base_search_service.py` - 已支援 `search_mode` 參數

### **測試工具**
- `test_stage2_full_search.sh` - 自動化測試腳本

---

## 🎉 結論

**方案 A-Enhanced 已完整實作並準備測試！**

請在瀏覽器中測試 Protocol Assistant Chat，發送查詢 "cup顏色"，並檢查日誌輸出。

如果看到上述所有預期日誌訊息，表示 Stage 2 已成功切換到全文搜尋模式 🎯

---

**實作日期**：2025-11-13  
**實作者**：AI Assistant  
**狀態**：✅ 實作完成，待測試驗證
