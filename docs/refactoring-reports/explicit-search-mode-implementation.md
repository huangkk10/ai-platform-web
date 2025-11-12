# 顯式 search_mode 參數實現報告

## 📋 實現目標

**問題**：原有 Mode B 兩層搜索使用「隱式控制」，透過修改查詢內容（加上「完整內容」）來期望 section 搜索失敗，進而觸發 fallback 到 document 搜索。這種方式不可靠且難以理解。

**解決方案**：實現顯式 `search_mode` 參數，允許上層直接指定搜索模式，無需依賴「意外失敗」機制。

---

## 🎯 search_mode 參數值

```python
search_mode = 'auto'           # 預設：section → document (自動 fallback)
search_mode = 'section_only'   # 僅搜索 section，不 fallback
search_mode = 'document_only'  # 跳過 section，直接搜索整篇文檔
search_mode = 'section_preferred'  # 同 'auto'（向後兼容）
search_mode = 'document_preferred'  # 偏好文檔（保留）
```

---

## 🏗️ 實現架構：5 個層級

### 層級 1：Dify Studio（inputs 參數）
```json
{
  "query": "如何連接 ULINK？",
  "inputs": {
    "search_mode": "document_only"
  }
}
```

### 層級 2：Django API Views
**檔案**：`backend/api/views/dify_knowledge_views.py`

```python
def external_knowledge_api(request):
    # 解析請求
    data = json.loads(request.body)
    inputs = data.get('inputs', {})
    
    # ✅ 提取 search_mode（預設為 'auto'）
    search_mode = inputs.get('search_mode', 'auto')
    
    # 傳遞給 handler
    result = handler.search(
        knowledge_id=knowledge_id,
        query=query,
        top_k=top_k,
        score_threshold=threshold,
        search_mode=search_mode  # ✅ 傳遞參數
    )
```

**修改內容**：
- ✅ 從 `inputs` 提取 `search_mode`
- ✅ 傳遞給 `handler.search()`
- ✅ 更新日誌顯示 mode

---

### 層級 3：Dify Knowledge Handler
**檔案**：`library/dify_knowledge/__init__.py`

#### 3.1 DifyKnowledgeSearchHandler.search()
```python
def search(self, knowledge_id, query, top_k=5, score_threshold=0.3, search_mode='auto'):
    """
    搜索知識庫
    
    Args:
        search_mode: 'auto', 'section_only', 'document_only'
    """
    self.logger.info(f"開始搜索: knowledge_id={knowledge_id}, mode={search_mode}")
    
    # 根據 knowledge_id 判斷知識類型
    knowledge_type = self._get_knowledge_type(knowledge_id)
    
    # 傳遞給下層
    results = self.search_knowledge_by_type(
        knowledge_type=knowledge_type,
        query=query,
        limit=top_k,
        threshold=score_threshold,
        search_mode=search_mode  # ✅ 傳遞參數
    )
```

#### 3.2 DifyKnowledgeSearchHandler.search_knowledge_by_type()
```python
def search_knowledge_by_type(self, knowledge_type, query, limit=5, threshold=0.3, search_mode='auto'):
    """
    根據知識類型執行搜索
    
    Args:
        search_mode: 搜索模式（'auto', 'section_only', 'document_only'）
    """
    self.logger.info(f"執行 {knowledge_type} 搜索 (mode={search_mode})")
    
    if knowledge_type == 'rvt_guide':
        if self.vector_search_available and self.search_rvt_guide_with_vectors:
            results = self.search_rvt_guide_with_vectors(
                query, 
                limit=limit, 
                threshold=threshold,
                search_mode=search_mode  # ✅ 傳遞參數
            )
            self.logger.info(f"RVT Guide 搜索結果: {len(results)} 條 (mode={search_mode})")
    
    elif knowledge_type == 'protocol_guide':
        results = self.search_protocol_guide_knowledge(
            query, 
            limit=limit, 
            threshold=threshold,
            search_mode=search_mode  # ✅ 傳遞參數
        )
        self.logger.info(f"Protocol Guide 搜索結果: {len(results)} 條 (mode={search_mode})")
    
    # ... 其他知識類型
```

**修改內容**：
- ✅ `search()` 添加 `search_mode='auto'` 參數
- ✅ `search_knowledge_by_type()` 添加 `search_mode='auto'` 參數
- ✅ 所有知識類型的搜索調用都傳遞 `search_mode`
- ✅ 更新日誌包含 mode 信息

---

### 層級 4：Knowledge Base Search Service
**檔案**：`library/common/knowledge_base/base_search_service.py`

#### 4.1 BaseKnowledgeBaseSearchService.search_knowledge()
```python
def search_knowledge(self, query, limit=5, threshold=0.3, search_mode='auto'):
    """
    智能搜索知識庫（向量 → 關鍵字 fallback）
    
    Args:
        search_mode: 'auto', 'section_only', 'document_only'
    """
    self.logger.info(f"開始搜索: query='{query}' (mode={search_mode})")
    
    # 嘗試向量搜索
    vector_results = self.search_with_vectors(
        query, 
        limit, 
        threshold=threshold,
        search_mode=search_mode  # ✅ 傳遞參數
    )
```

#### 4.2 BaseKnowledgeBaseSearchService.search_with_vectors()
```python
def search_with_vectors(self, query, limit=5, threshold=0.0, search_mode='auto'):
    """
    使用向量搜索知識庫（支援 section → document fallback）
    
    Args:
        search_mode: 搜索模式
            - 'auto'/'section_preferred': section → document (自動 fallback)
            - 'section_only': 僅搜索 section，不 fallback
            - 'document_only': 跳過 section，直接搜索整篇文檔
    """
    self.logger.info(f"向量搜索 (mode={search_mode}): {self.source_table}")
    
    # 模式 1: document_only - 直接搜索整篇文檔
    if search_mode == 'document_only':
        self.logger.info(f"🎯 Mode=document_only，跳過 section，直接搜索整篇文檔")
        return self.search_with_vectors_generic(
            query=query,
            source_table=self.source_table,
            limit=limit,
            threshold=threshold
        )
    
    # 模式 2: section_only - 僅搜索 section，不 fallback
    if search_mode == 'section_only':
        self.logger.info(f"🔍 Mode=section_only，僅搜索 section")
        section_results = self.search_sections(
            query=query,
            limit=limit,
            threshold=threshold
        )
        self.logger.info(f"✅ Section 搜索完成: {len(section_results)} 條（無 fallback）")
        return section_results
    
    # 模式 3: auto/section_preferred - 自動 fallback
    self.logger.info(f"🔄 Mode={search_mode}，嘗試 section 搜索（允許 fallback）")
    
    # 步驟 1: 嘗試 section 搜索
    section_results = self.search_sections(
        query=query,
        limit=limit,
        threshold=threshold
    )
    
    # 步驟 2: 如果 section 無結果，fallback 到整篇文檔
    if not section_results:
        self.logger.warning(f"⚠️ Section 搜索無結果，fallback 到整篇文檔搜索")
        return self.search_with_vectors_generic(
            query=query,
            source_table=self.source_table,
            limit=limit,
            threshold=threshold
        )
    
    return section_results
```

**修改內容**：
- ✅ `search_knowledge()` 添加 `search_mode='auto'` 參數
- ✅ `search_with_vectors()` 添加 `search_mode='auto'` 參數
- ✅ 實現 3 種模式的分支邏輯
- ✅ 詳細的日誌記錄每個步驟

---

### 層級 5：Two-Tier Handler（RVT Guide Mode B）
**檔案**：`library/rvt_guide/two_tier_handler.py`

```python
def _request_dify_chat(self, query: str, conversation_id: str = None, is_full_search: bool = False):
    """
    發送請求到 Dify
    
    Args:
        is_full_search: 是否為第二階段（document-level 搜索）
    """
    # ✅ 移除查詢重寫邏輯（不再需要）
    # ❌ 舊代碼：if is_full_search: query = f"{query} 完整內容"
    
    # ✅ 新方式：使用 inputs 傳遞 search_mode
    if is_full_search:
        # Stage 2: 直接指定 document_only 模式
        inputs = {
            'search_mode': 'document_only',
            'require_detailed_answer': 'true'
        }
        self.logger.info(f"📊 Stage 2: Document-level 搜索 (mode=document_only)")
    else:
        # Stage 1: 使用預設的 auto 模式
        inputs = {
            'search_mode': 'auto'
        }
        self.logger.info(f"🔍 Stage 1: Section-level 搜索 (mode=auto)")
    
    # 調用 Dify API
    response = requests.post(
        url=dify_config.api_url,
        json={
            'query': query,  # ✅ 查詢內容保持不變
            'conversation_id': conversation_id,
            'user': user_id,
            'inputs': inputs  # ✅ 透過 inputs 傳遞 search_mode
        }
    )
```

**關鍵改變**：
- ❌ **移除**：查詢重寫邏輯 `query = f"{query} 完整內容"`
- ✅ **新增**：使用 `inputs` 傳遞 `search_mode`
- ✅ Stage 1：`search_mode: 'auto'`（section → document fallback）
- ✅ Stage 2：`search_mode: 'document_only'`（直接 document 搜索）
- ✅ 查詢內容在兩個階段保持一致（不再修改）

---

## 📊 參數流動完整路徑

```
Dify Studio
  ↓ inputs: { search_mode: 'document_only' }
  
Django API (dify_knowledge_views.py)
  ↓ search_mode = inputs.get('search_mode', 'auto')
  
DifyKnowledgeSearchHandler.search()
  ↓ search_mode='document_only'
  
DifyKnowledgeSearchHandler.search_knowledge_by_type()
  ↓ search_mode='document_only'
  
RVTGuideSearchService.search_knowledge()
  ↓ search_mode='document_only'
  (繼承自 BaseKnowledgeBaseSearchService)
  
BaseKnowledgeBaseSearchService.search_with_vectors()
  ↓ if search_mode == 'document_only':
  
BaseKnowledgeBaseSearchService.search_with_vectors_generic()
  ↓ 直接查詢 document_embeddings 表
  
PostgreSQL
  ✅ 返回整篇文檔的向量搜索結果
```

---

## ✅ 修改文件清單

| 檔案 | 狀態 | 修改內容 |
|------|------|---------|
| `library/common/knowledge_base/base_search_service.py` | ✅ 完成 | search_with_vectors() 添加 search_mode 參數和分支邏輯 |
| `library/common/knowledge_base/base_search_service.py` | ✅ 完成 | search_knowledge() 添加 search_mode 參數 |
| `library/rvt_guide/two_tier_handler.py` | ✅ 完成 | 移除查詢重寫，改用 inputs 傳遞 search_mode |
| `library/dify_knowledge/__init__.py` | ✅ 完成 | search() 方法添加 search_mode 參數 |
| `library/dify_knowledge/__init__.py` | ✅ 完成 | search_knowledge_by_type() 添加 search_mode 參數 |
| `backend/api/views/dify_knowledge_views.py` | ✅ 完成 | 從 inputs 提取 search_mode 並傳遞給 handler |

---

## 🧪 測試計劃

### 測試 1：Mode 'auto'（預設行為）
```python
# 測試預設行為保持不變
response = requests.post('/api/dify/knowledge/retrieval/', json={
    'knowledge_id': 'rvt_guide',
    'query': '如何連接 ULINK？',
    'inputs': {
        'search_mode': 'auto'
    }
})

# 預期：
# 1. 先嘗試 section 搜索
# 2. 如果無結果，fallback 到 document 搜索
```

### 測試 2：Mode 'document_only'
```python
# 測試直接 document 搜索
response = requests.post('/api/dify/knowledge/retrieval/', json={
    'knowledge_id': 'rvt_guide',
    'query': 'ULINK 完整設置流程',
    'inputs': {
        'search_mode': 'document_only'
    }
})

# 預期：
# 1. 跳過 section 搜索
# 2. 直接執行 document 搜索
# 3. 日誌顯示：Mode=document_only，跳過 section
```

### 測試 3：Mode 'section_only'
```python
# 測試僅 section 搜索
response = requests.post('/api/dify/knowledge/retrieval/', json={
    'knowledge_id': 'rvt_guide',
    'query': '連接步驟',
    'inputs': {
        'search_mode': 'section_only'
    }
})

# 預期：
# 1. 僅執行 section 搜索
# 2. 即使無結果，也不 fallback
# 3. 可能返回空結果
```

### 測試 4：RVT Guide Mode B 兩層搜索
```python
# 測試 RVT Assistant 的 Mode B
# Stage 1: 自動發送 search_mode='auto'
# Stage 2: 自動發送 search_mode='document_only'

response = requests.post('/api/rvt-guide/chat/', json={
    'message': '如何進行 RVT 測試？',
    'conversation_id': None
})

# 檢查日誌：
# Stage 1: mode=auto, 查詢內容未修改
# Stage 2: mode=document_only, 查詢內容未修改
```

---

## 📈 效能影響

### 正面影響
- ✅ **減少無效查詢**：document_only 模式跳過 section 搜索
- ✅ **更清晰的邏輯**：不再依賴「意外失敗」機制
- ✅ **更好的日誌**：每個模式都有明確的日誌記錄

### 中性影響
- ➡️ **查詢時間**：auto 模式與原有邏輯相同
- ➡️ **向後兼容**：預設 'auto' 保持原有行為

---

## 🎓 使用指南

### 在 Dify Studio 中設定

1. **打開 Dify 工作室**
2. **進入 RVT Guide 應用**
3. **編排頁面 → 外部知識庫節點**
4. **添加變量**：
   ```json
   {
     "search_mode": {
       "type": "string",
       "default": "auto",
       "options": ["auto", "section_only", "document_only"]
     }
   }
   ```

5. **在不同階段設定不同值**：
   - Stage 1（首次查詢）：`search_mode = "auto"`
   - Stage 2（需要完整內容）：`search_mode = "document_only"`

---

## 🔮 未來擴展

### 可能的新模式
```python
search_mode = 'hybrid'           # 同時搜索 section + document，合併結果
search_mode = 'keyword_only'     # 僅使用關鍵字搜索，不用向量
search_mode = 'vector_only'      # 僅使用向量搜索，不 fallback 到關鍵字
```

### 可能的高級參數
```json
{
  "search_mode": "auto",
  "fallback_threshold": 0.5,     // 低於此值時觸發 fallback
  "section_limit": 10,            // section 搜索的 limit
  "document_limit": 5             // document 搜索的 limit
}
```

---

## 📚 相關文檔

- **查詢重寫分析**：`/docs/architecture/query-rewriting-analysis.md`
- **兩層搜索機制**：`/docs/architecture/mode-b-two-tier-search-flow.md`
- **向量搜索架構**：`/docs/architecture/rvt-assistant-database-vector-architecture.md`

---

**日期**：2025-01-20  
**版本**：v1.0  
**狀態**：✅ 實現完成，待測試  
**負責人**：AI Platform Team
