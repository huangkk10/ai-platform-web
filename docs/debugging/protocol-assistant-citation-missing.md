# Protocol Assistant 引用來源缺失問題分析

**問題日期**：2025-11-10  
**問題描述**：用戶詢問「Cup」檔案，AI 找到並引用了其他檔案（ISC 進階問題 82%, Burn in Test 81%），但引用來源中沒有顯示 "Cup" 這份檔案。

---

## 🔍 問題診斷

### 1️⃣ **資料庫檢查結果**

#### ✅ Protocol Guide 資料存在
```sql
SELECT id, title, content FROM protocol_guide WHERE id=19;
```
**結果**：
- ID: 19
- Title: "Cup"
- Content: "a" （只有一個字母）

#### ✅ 整篇文檔向量存在
```sql
SELECT COUNT(*), vector_dims(embedding) 
FROM document_embeddings 
WHERE source_table='protocol_guide' AND source_id=19;
```
**結果**：
- Count: 1
- Dimension: 1024 ✅

#### ❌ **Section 向量不存在！**
```sql
SELECT * FROM document_section_embeddings
WHERE source_table='protocol_guide' AND document_id='19';
```
**結果**：
- Count: 0 ❌

---

## 🎯 根本原因

### 問題 1：內容太短，無法生成 Sections

"Cup" 檔案的內容只有一個字母 "a"，**沒有 Markdown 標題結構**，導致：

1. **Section 分割失敗**
   ```python
   # SectionVectorizationService.vectorize_document_sections()
   # 需要識別 Markdown 標題（# ## ###）來分割 sections
   # 但 "a" 沒有任何標題，無法分割
   ```

2. **Section 向量無法生成**
   - `document_section_embeddings` 表中沒有記錄
   - 導致向量搜尋無法找到此檔案

3. **為什麼整篇向量存在？**
   - 整篇文檔向量（`document_embeddings`）不需要 sections
   - 即使內容只有 "a"，仍會生成向量
   - 但這個向量可能沒有被使用（因為新系統優先使用 section 向量）

---

### 問題 2：搜尋系統只使用 Section 向量

**當前 Protocol Assistant 的搜尋邏輯**：

```python
# library/protocol_guide/search_service.py
class ProtocolGuideSearchService(BaseKnowledgeBaseSearchService):
    source_table = 'protocol_guide'
    
    # 搜尋時使用 document_section_embeddings
    def search_knowledge(self, query, ...):
        # 向量搜尋查詢 document_section_embeddings
        # 如果檔案沒有 sections，就無法被搜尋到
```

**為什麼其他檔案可以被找到？**
- "ISC 進階問題" - 有完整的 Markdown 結構 ✅
- "Burn in Test" - 有完整的 Markdown 結構 ✅
- "Cup" - 沒有 Markdown 結構 ❌

---

## 🔧 解決方案

### 方案 1：補充檔案內容（推薦）

**建議用戶**：
1. 編輯 "Cup" 檔案，添加實際內容和 Markdown 標題結構
2. 例如：
   ```markdown
   # Cup 介紹
   
   ## 基本資訊
   Cup 是...
   
   ## 使用方法
   1. 步驟一
   2. 步驟二
   ```

3. 更新後，系統會自動重新生成 section 向量 ✅

---

### 方案 2：啟用 Fallback 到整篇向量（需要代碼修改）

如果需要支援**無 Markdown 結構的檔案**，需要修改搜尋邏輯：

```python
# library/protocol_guide/search_service.py

def search_knowledge(self, query: str, limit: int = 5, use_vector: bool = True, 
                    threshold: float = 0.7) -> list:
    """
    增強：如果 section 搜尋無結果，fallback 到整篇文檔向量
    """
    # 步驟 1: 分類查詢
    query_type = self._classify_query(query)
    
    # 步驟 2: 執行 section 級搜尋
    results = super().search_knowledge(
        query=query,
        limit=limit,
        use_vector=use_vector,
        threshold=threshold
    )
    
    # 🆕 步驟 2.5: 如果 section 搜尋無結果，fallback 到整篇向量
    if not results and use_vector:
        logger.info("⚠️  Section 搜尋無結果，嘗試整篇文檔向量...")
        results = self._fallback_to_full_document_vectors(query, limit, threshold)
    
    # 步驟 3: 如果是文檔級查詢，擴展為完整文檔
    if query_type == 'document' and results:
        logger.info(f"🔄 將 {len(results)} 個結果擴展為完整文檔")
        results = self._expand_to_full_document(results)
    
    return results

def _fallback_to_full_document_vectors(self, query: str, limit: int, threshold: float) -> list:
    """
    Fallback: 使用整篇文檔向量搜尋（document_embeddings）
    """
    from api.services.embedding_service import get_embedding_service
    
    try:
        embedding_service = get_embedding_service()
        
        # 使用整篇文檔向量搜尋
        results = embedding_service.semantic_search(
            query=query,
            source_table=self.source_table,
            top_k=limit,
            threshold=threshold,
            use_1024_table=True  # 使用 document_embeddings
        )
        
        logger.info(f"✅ 整篇向量搜尋返回 {len(results)} 個結果")
        return results
        
    except Exception as e:
        logger.error(f"❌ 整篇向量搜尋失敗: {str(e)}")
        return []
```

---

### 方案 3：修復現有資料（臨時補救）

**手動為 "Cup" 生成 section 資料**：

```python
# 進入 Django shell
docker exec -it ai-django python manage.py shell

# 執行以下代碼
from api.models import ProtocolGuide
from library.common.knowledge_base.section_vectorization_service import SectionVectorizationService

# 獲取 Cup 檔案
cup = ProtocolGuide.objects.get(id=19)

# 如果內容太短，先添加一些結構
cup.content = """# Cup 介紹

## 基本資訊
Cup 相關資訊。

## 詳細說明
待補充...
"""
cup.save()

# 手動生成 section 向量
vectorization_service = SectionVectorizationService()
result = vectorization_service.vectorize_document_sections(
    source_table='protocol_guide',
    source_id=19,
    markdown_content=cup.content,
    metadata={'title': cup.title}
)

print(f"✅ 生成 {result} 個 sections")
```

---

## 📊 驗證方法

### 檢查 "Cup" 的 Section 向量

```bash
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT 
    id,
    heading_text,
    is_document_title,
    LENGTH(content) as content_length,
    vector_dims(embedding) as dimension
FROM document_section_embeddings
WHERE source_table='protocol_guide' 
    AND document_id='19';
"
```

**預期結果（修復後）**：
```
id | heading_text | is_document_title | content_length | dimension
----+--------------+-------------------+----------------+-----------
123 | Cup 介紹     | false             | 50             | 1024
124 | 基本資訊     | false             | 100            | 1024
125 | 詳細說明     | false             | 80             | 1024
```

### 測試搜尋

```bash
curl -X POST "http://localhost/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "protocol_guide_db",
    "query": "Cup",
    "retrieval_setting": {"top_k": 3, "score_threshold": 0.5}
  }' | python3 -m json.tool
```

**預期結果（修復後）**：
```json
{
  "records": [
    {
      "content": "# Cup 介紹\n\n## 基本資訊\nCup 相關資訊。\n\n## 詳細說明\n待補充...",
      "score": 0.95,
      "title": "Cup",
      "metadata": {
        "document_id": "19",
        "source_table": "protocol_guide"
      }
    }
  ]
}
```

---

## 🎯 總結

### 問題本質

**"Cup" 檔案在引用來源中消失的原因**：

1. ❌ **內容太短且無結構**：只有一個字母 "a"
2. ❌ **無 Markdown 標題**：無法分割成 sections
3. ❌ **Section 向量缺失**：`document_section_embeddings` 中沒有記錄
4. ❌ **搜尋系統限制**：只使用 section 向量，不會 fallback 到整篇向量

### 為什麼整篇向量沒用？

- 整篇向量（`document_embeddings`）確實存在 ✅
- 但**新的搜尋系統優先使用 section 向量**（更精確）
- 當 section 向量不存在時，**不會自動 fallback** ❌
- 導致內容太短的檔案無法被搜尋到

### 推薦解決方案

**短期**（立即生效）：
- 編輯 "Cup" 檔案，添加 Markdown 結構內容 ✅
- 系統會自動重新生成 section 向量

**長期**（改善系統）：
- 實作 Fallback 機制（方案 2）
- 當 section 搜尋無結果時，自動嘗試整篇向量
- 提升系統對短內容檔案的支援度

---

## 📚 相關文檔

- **文檔級搜尋架構**：`/docs/architecture/document-level-search-architecture.md`
- **向量生成指南**：`/docs/vector-search/protocol-guide-vector-auto-generation.md`
- **Section 向量系統**：`/docs/architecture/multi-vector-storage-architecture.md`

---

**診斷日期**：2025-11-10  
**分析者**：AI Platform Team  
**狀態**：✅ 已診斷完成，待用戶選擇解決方案
