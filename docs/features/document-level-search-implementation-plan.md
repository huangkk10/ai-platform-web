# 文檔級搜尋功能實施計畫

## 📋 專案資訊
- **創建日期**: 2025-11-10
- **問題描述**: SOP 文檔在搜尋時被截斷，只返回單個 section 內容（如 332 字元），導致 AI 無法理解完整 SOP 流程
- **目標**: 實現智能的文檔級搜尋，當查詢 SOP 類文檔時返回完整內容，其他查詢保持 section 級搜尋
- **實施範圍**: **只需要修改 Backend**，Frontend 不需要任何改動

---

## 🎯 核心設計原則

### 為什麼 Frontend 不需要修改？

**現有資料流程**：
```
User Query → Frontend → Backend API → Dify API
                                         ↓
                                    向 Django 外部知識庫 API 請求
                                         ↓
                                    接收多個 records (content, score, title)
                                         ↓
                                    LLM 整合所有 records 生成回答
                                         ↓
Frontend ← Backend API ← Dify API (返回 answer 文本)
         ↓
     直接顯示 data.answer
```

**關鍵發現**：
1. Frontend 只接收 `{ answer: "..." }` 並直接顯示
2. 所有「內容整合」邏輯都在 **Dify 端的 LLM** 處理
3. Backend 只負責提供搜尋結果給 Dify，不負責組合答案
4. 因此，只需要改變「Backend 返回什麼內容」，不需要改 Frontend

---

## 📊 問題分析

### 現況問題

**範例查詢**: "IOL 放測 SOP"

**當前行為**：
```
1. 向量搜尋找到最相關的 Section 3: "IOL放測"
2. 上下文擴展找到 Section 3 的子 sections (sec_4, sec_5)
3. 返回給 Dify:
   - Section 3 content (主要內容)
   - Section 3.1 content (子內容 1)
   - Section 3.2 content (子內容 2)
4. 總字數: 約 332 字元 (只是 Section 3 的範圍)
5. 遺失: Sections 1, 2, 4-7 (前言、準備、後續步驟等)
```

**問題影響**：
- ❌ AI 看不到 SOP 的完整流程
- ❌ 無法理解前置條件和後續步驟
- ❌ 回答可能遺漏關鍵資訊

### 期望行為

**範例查詢**: "IOL 放測 SOP"

**期望行為**：
```
1. 智能判斷：這是 SOP 類查詢
2. 返回完整文檔內容（所有 sections 1-7）
3. 組織格式：
   # UNH-IOL (Broadcom) 放測 SOP
   
   ## 1. Section 1 Title
   Section 1 content...
   
   ## 2. Section 2 Title
   Section 2 content...
   
   ... (所有 sections)
4. 總字數: 完整文檔 (例如 2000+ 字元)
5. AI 能看到完整 SOP 流程並給出完整回答
```

---

## 🏗️ 技術架構設計

### 資料庫架構升級

**目標**: 在現有 `document_section_embeddings` 表中添加文檔層級資訊

**新增欄位**：
```sql
ALTER TABLE document_section_embeddings ADD COLUMN document_id VARCHAR(100);
ALTER TABLE document_section_embeddings ADD COLUMN document_title TEXT;
ALTER TABLE document_section_embeddings ADD COLUMN is_document_title BOOLEAN DEFAULT FALSE;

-- 索引優化
CREATE INDEX idx_document_section_embeddings_doc_id ON document_section_embeddings(document_id);
CREATE INDEX idx_document_section_embeddings_is_doc_title ON document_section_embeddings(is_document_title);
```

**資料結構範例**：
```
section_id  | document_id | document_title                   | is_document_title | heading_level | parent_section_id
------------|-------------|----------------------------------|-------------------|---------------|------------------
doc_1       | doc_1       | UNH-IOL (Broadcom) 放測 SOP      | TRUE              | 0             | NULL
sec_1       | doc_1       | UNH-IOL (Broadcom) 放測 SOP      | FALSE             | 1             | NULL
sec_2       | doc_1       | UNH-IOL (Broadcom) 放測 SOP      | FALSE             | 1             | NULL
sec_3       | doc_1       | UNH-IOL (Broadcom) 放測 SOP      | FALSE             | 1             | NULL
sec_4       | doc_1       | UNH-IOL (Broadcom) 放測 SOP      | FALSE             | 2             | sec_3
```

**層級關係**：
- **Level 0**: Document Title (文檔標題，is_document_title=TRUE)
- **Level 1**: Top-level Sections (一級章節，parent_section_id=NULL)
- **Level 2+**: Subsections (子章節，parent_section_id != NULL)

### 搜尋邏輯升級

**核心策略**: 智能判斷查詢類型，動態調整返回範圍

```python
# library/protocol_guide/search_service.py

class ProtocolGuideSearchService:
    
    def search_knowledge(self, query, limit=5):
        """
        智能搜尋主函數
        
        流程:
        1. 執行向量搜尋
        2. 判斷查詢類型
        3. 動態擴展內容
        4. 返回給 Dify
        """
        # Step 1: 向量搜尋
        search_results = self._vector_search(query, limit)
        
        if not search_results:
            return []
        
        # Step 2: 智能判斷
        query_type = self._classify_query(query, search_results)
        
        # Step 3: 根據類型擴展內容
        if query_type == 'FULL_DOCUMENT':
            return self._expand_to_full_document(search_results)
        elif query_type == 'SECTION_WITH_CONTEXT':
            return self._expand_with_context(search_results)
        else:
            return search_results
    
    def _classify_query(self, query, results):
        """
        分類查詢類型
        
        判斷邏輯:
        - 關鍵詞匹配: SOP, 流程, 步驟, 指南, 教學
        - 命中文檔標題: is_document_title=TRUE
        - 高相似度: score > 0.85
        """
        # 1. 關鍵詞匹配
        sop_keywords = ['sop', 'SOP', '流程', '步驟', '指南', '教學', '操作', '如何']
        if any(keyword in query for keyword in sop_keywords):
            return 'FULL_DOCUMENT'
        
        # 2. 命中文檔標題
        top_result = results[0]
        if top_result.get('is_document_title', False):
            return 'FULL_DOCUMENT'
        
        # 3. 高相似度且是頂層 section
        if top_result.get('score', 0) > 0.85 and top_result.get('heading_level', 99) == 1:
            # 檢查是否為 SOP 類文檔
            doc_title = top_result.get('document_title', '').lower()
            if 'sop' in doc_title or '流程' in doc_title:
                return 'FULL_DOCUMENT'
        
        # 4. 預設：section + context
        return 'SECTION_WITH_CONTEXT'
    
    def _expand_to_full_document(self, results):
        """
        擴展到完整文檔
        
        步驟:
        1. 從 top result 取得 document_id
        2. 查詢該文檔的所有 sections (依 heading_level + 順序)
        3. 組合成完整 Markdown 格式
        4. 返回單個 record (content = 完整文檔)
        """
        doc_id = results[0].get('document_id')
        doc_title = results[0].get('document_title')
        
        # 查詢所有 sections (排序: heading_level ASC, section_id ASC)
        all_sections = DocumentSectionEmbedding.objects.filter(
            document_id=doc_id,
            is_document_title=False
        ).order_by('heading_level', 'section_id')
        
        # 組合完整內容
        full_content = f"# {doc_title}\n\n"
        
        for section in all_sections:
            # 根據 heading_level 決定 Markdown 標題等級
            heading_prefix = '#' * (section.heading_level + 1)
            full_content += f"{heading_prefix} {section.section_title}\n\n"
            full_content += f"{section.text_content}\n\n"
        
        # 返回單個 record (Dify 會收到完整文檔)
        return [{
            'content': full_content,
            'score': results[0]['score'],
            'title': doc_title,
            'metadata': {
                'type': 'full_document',
                'document_id': doc_id,
                'section_count': all_sections.count(),
                'total_length': len(full_content)
            }
        }]
    
    def _expand_with_context(self, results):
        """
        擴展到 section + context (現有邏輯)
        
        保持現有的上下文視窗擴展邏輯:
        - Adjacent sections
        - Hierarchical parent/children
        - Empty section child expansion
        """
        # 使用現有的 ContextWindowService
        from library.protocol_guide.context_window_service import ContextWindowService
        
        context_service = ContextWindowService()
        expanded_results = []
        
        for result in results:
            expanded = context_service.expand_context(
                section_id=result['section_id'],
                mode='both',  # adjacent + hierarchical
                max_tokens=4000
            )
            expanded_results.append(expanded)
        
        return expanded_results
```

---

## 📝 實施步驟

### Phase 1: 資料庫結構升級 ⏱️ 預計 2-3 小時

#### 1.1 添加新欄位
```sql
-- 檔案: backend/scripts/add_document_level_fields.sql

-- 添加文檔層級欄位
ALTER TABLE document_section_embeddings 
ADD COLUMN IF NOT EXISTS document_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS document_title TEXT,
ADD COLUMN IF NOT EXISTS is_document_title BOOLEAN DEFAULT FALSE;

-- 創建索引
CREATE INDEX IF NOT EXISTS idx_document_section_embeddings_doc_id 
    ON document_section_embeddings(document_id);

CREATE INDEX IF NOT EXISTS idx_document_section_embeddings_is_doc_title 
    ON document_section_embeddings(is_document_title);

-- 驗證
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'document_section_embeddings' 
    AND column_name IN ('document_id', 'document_title', 'is_document_title');
```

**執行指令**：
```bash
docker exec postgres_db psql -U postgres -d ai_platform -f /path/to/add_document_level_fields.sql
```

#### 1.2 填充現有資料

**策略**: 從 `protocol_guide` 表中提取文檔資訊，回填到 `document_section_embeddings`

```python
# backend/scripts/populate_document_fields.py

import sys
import os
import django

# Django setup
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from django.db import connection, transaction
from api.models import ProtocolGuide

def populate_document_fields():
    """填充文檔層級欄位"""
    
    with connection.cursor() as cursor:
        # 1. 獲取所有 protocol_guide 記錄
        guides = ProtocolGuide.objects.all()
        
        updated_count = 0
        
        for guide in guides:
            guide_id = guide.id
            guide_title = guide.title
            
            # 2. 更新該 guide 下的所有 section embeddings
            cursor.execute("""
                UPDATE document_section_embeddings
                SET 
                    document_id = %s,
                    document_title = %s
                WHERE source_table = 'protocol_guide'
                    AND source_id = %s
                    AND is_document_title = FALSE
            """, [f"doc_{guide_id}", guide_title, guide_id])
            
            updated_count += cursor.rowcount
            print(f"✅ Updated {cursor.rowcount} sections for guide {guide_id}: {guide_title}")
        
        # 3. 創建文檔標題記錄 (is_document_title=TRUE)
        for guide in guides:
            # 檢查是否已存在文檔標題記錄
            cursor.execute("""
                SELECT COUNT(*) FROM document_section_embeddings
                WHERE document_id = %s AND is_document_title = TRUE
            """, [f"doc_{guide.id}"])
            
            if cursor.fetchone()[0] == 0:
                # 創建文檔標題向量 (使用標題文本)
                from api.services.embedding_service import get_embedding_service
                service = get_embedding_service()
                
                title_embedding = service.generate_embedding(guide.title)
                
                cursor.execute("""
                    INSERT INTO document_section_embeddings 
                    (source_table, source_id, document_id, document_title, 
                     is_document_title, section_id, section_title, text_content, 
                     embedding, heading_level, parent_section_id)
                    VALUES 
                    (%s, %s, %s, %s, TRUE, %s, %s, %s, %s, 0, NULL)
                """, [
                    'protocol_guide',
                    guide.id,
                    f"doc_{guide.id}",
                    guide.title,
                    f"doc_{guide.id}",  # section_id
                    guide.title,        # section_title
                    guide.title,        # text_content
                    title_embedding     # embedding
                ])
                
                print(f"✅ Created document title record for guide {guide.id}")
        
        print(f"\n🎉 Total updated: {updated_count} section records")
        print(f"🎉 Created {guides.count()} document title records")

if __name__ == '__main__':
    with transaction.atomic():
        populate_document_fields()
```

**執行指令**：
```bash
docker exec ai-django python /app/scripts/populate_document_fields.py
```

#### 1.3 驗證資料

```sql
-- 檔案: backend/scripts/verify_document_fields.sql

-- 1. 檢查欄位是否存在
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'document_section_embeddings' 
    AND column_name IN ('document_id', 'document_title', 'is_document_title');

-- 2. 檢查資料填充情況
SELECT 
    source_table,
    COUNT(*) as total_records,
    COUNT(document_id) as has_document_id,
    COUNT(document_title) as has_document_title,
    SUM(CASE WHEN is_document_title THEN 1 ELSE 0 END) as document_title_records
FROM document_section_embeddings
GROUP BY source_table;

-- 3. 檢查文檔層級結構
SELECT 
    document_id,
    document_title,
    COUNT(*) as section_count,
    SUM(CASE WHEN is_document_title THEN 1 ELSE 0 END) as has_title_record,
    COUNT(DISTINCT heading_level) as level_count
FROM document_section_embeddings
WHERE source_table = 'protocol_guide'
GROUP BY document_id, document_title
ORDER BY document_id;

-- 4. 查看範例記錄
SELECT 
    section_id,
    document_id,
    document_title,
    is_document_title,
    heading_level,
    section_title,
    LENGTH(text_content) as content_length
FROM document_section_embeddings
WHERE document_id = 'doc_1'  -- UNH-IOL 文檔
ORDER BY is_document_title DESC, heading_level, section_id
LIMIT 20;
```

**預期結果**：
```
# 1. 欄位存在
document_id       | character varying(100)
document_title    | text
is_document_title | boolean

# 2. 資料填充情況
source_table    | total_records | has_document_id | has_document_title | document_title_records
protocol_guide  | 150           | 150             | 150                | 15

# 3. 文檔結構
document_id | document_title                  | section_count | has_title_record | level_count
doc_1       | UNH-IOL (Broadcom) 放測 SOP     | 11            | 1                | 3

# 4. 範例記錄
section_id | document_id | document_title              | is_document_title | heading_level | section_title
doc_1      | doc_1       | UNH-IOL (Broadcom) 放測 SOP | TRUE              | 0             | UNH-IOL...
sec_1      | doc_1       | UNH-IOL (Broadcom) 放測 SOP | FALSE             | 1             | Section 1
sec_2      | doc_1       | UNH-IOL (Broadcom) 放測 SOP | FALSE             | 1             | Section 2
...
```

---

### Phase 2: 搜尋邏輯升級 ⏱️ 預計 4-5 小時

#### 2.1 更新 Search Service

**檔案**: `library/protocol_guide/search_service.py`

**修改點**：
1. 添加 `_classify_query()` - 查詢類型分類
2. 添加 `_expand_to_full_document()` - 完整文檔擴展
3. 修改 `search_knowledge()` - 整合新邏輯
4. 保留 `_expand_with_context()` - 現有上下文擴展

**關鍵程式碼** (詳見上方「搜尋邏輯升級」章節)

#### 2.2 更新 Model (可選)

如果 Django Model 需要反映新欄位：

```python
# api/models.py (或對應的 Model 檔案)

class DocumentSectionEmbedding(models.Model):
    # ... 現有欄位 ...
    
    # ✅ 新增欄位
    document_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    document_title = models.TextField(null=True, blank=True)
    is_document_title = models.BooleanField(default=False, db_index=True)
    
    class Meta:
        db_table = 'document_section_embeddings'
        indexes = [
            models.Index(fields=['document_id']),
            models.Index(fields=['is_document_title']),
        ]
```

**執行 Migration**：
```bash
docker exec ai-django python manage.py makemigrations
docker exec ai-django python manage.py migrate
```

#### 2.3 更新 API Handler (如需要)

**檔案**: `library/protocol_guide/api_handlers.py`

**確認點**：
- `ProtocolGuideAPIHandler` 是否需要特殊邏輯？
- 大部分邏輯在 `SearchService` 中，API Handler 通常不需要改動

---

### Phase 3: 測試驗證 ⏱️ 預計 2-3 小時

#### 3.1 單元測試

**檔案**: `tests/test_document_level_search.py`

```python
import pytest
from django.test import TestCase
from library.protocol_guide.search_service import ProtocolGuideSearchService

class TestDocumentLevelSearch(TestCase):
    """測試文檔級搜尋功能"""
    
    def setUp(self):
        self.search_service = ProtocolGuideSearchService()
    
    def test_sop_query_returns_full_document(self):
        """測試 SOP 查詢返回完整文檔"""
        query = "IOL 放測 SOP"
        results = self.search_service.search_knowledge(query, limit=1)
        
        # 驗證
        assert len(results) == 1
        result = results[0]
        
        # 應該返回完整文檔
        assert result['metadata']['type'] == 'full_document'
        assert 'UNH-IOL' in result['title']
        assert len(result['content']) > 1000  # 完整文檔應該較長
        
        # 應該包含多個 sections
        assert result['metadata']['section_count'] >= 7
    
    def test_section_query_returns_context(self):
        """測試一般查詢返回 section + context"""
        query = "如何配置網路設定"
        results = self.search_service.search_knowledge(query, limit=3)
        
        # 驗證
        assert len(results) > 0
        
        # 應該是 section 級別，不是完整文檔
        for result in results:
            assert result['metadata']['type'] != 'full_document'
    
    def test_document_title_match(self):
        """測試命中文檔標題"""
        query = "UNH-IOL Broadcom"
        results = self.search_service.search_knowledge(query, limit=1)
        
        # 應該命中文檔標題並返回完整文檔
        assert len(results) == 1
        assert results[0]['metadata']['type'] == 'full_document'
    
    def test_classify_query_sop_keywords(self):
        """測試查詢分類 - SOP 關鍵詞"""
        service = ProtocolGuideSearchService()
        
        # SOP 關鍵詞應該觸發 FULL_DOCUMENT
        test_cases = [
            ("XXX SOP", "FULL_DOCUMENT"),
            ("如何操作 YYY", "FULL_DOCUMENT"),
            ("ZZZ 流程指南", "FULL_DOCUMENT"),
            ("一般查詢問題", "SECTION_WITH_CONTEXT"),
        ]
        
        for query, expected_type in test_cases:
            # 模擬搜尋結果
            mock_results = [{'score': 0.8, 'heading_level': 1}]
            query_type = service._classify_query(query, mock_results)
            assert query_type == expected_type, f"Query '{query}' should be {expected_type}"
```

**執行測試**：
```bash
docker exec ai-django python -m pytest tests/test_document_level_search.py -v
```

#### 3.2 整合測試

**檔案**: `tests/test_document_search_integration.py`

```python
def test_full_search_pipeline():
    """測試完整搜尋流程：DB → Search Service → Dify API"""
    
    # 1. 資料庫驗證
    from api.models import DocumentSectionEmbedding
    doc_sections = DocumentSectionEmbedding.objects.filter(
        document_id='doc_1',
        source_table='protocol_guide'
    )
    assert doc_sections.exists()
    assert doc_sections.filter(is_document_title=True).count() == 1
    
    # 2. Search Service 驗證
    from library.protocol_guide.search_service import ProtocolGuideSearchService
    service = ProtocolGuideSearchService()
    results = service.search_knowledge("IOL 放測 SOP", limit=1)
    assert len(results) == 1
    assert results[0]['metadata']['type'] == 'full_document'
    
    # 3. API 端點驗證
    from django.test import Client
    client = Client()
    response = client.post('/api/dify/protocol-guide/search/', {
        'query': 'IOL 放測 SOP',
        'knowledge_id': 'protocol_guide_db',
        'retrieval_setting': {'top_k': 1, 'score_threshold': 0.5}
    }, content_type='application/json')
    
    assert response.status_code == 200
    data = response.json()
    assert 'records' in data
    assert len(data['records']) > 0
    
    # 4. 內容驗證
    record = data['records'][0]
    assert len(record['content']) > 1000  # 完整文檔
    assert 'UNH-IOL' in record['title']
    
    print("✅ Full search pipeline test passed!")
```

#### 3.3 手動測試腳本

**檔案**: `backend/test_document_level_search_manual.py`

```python
#!/usr/bin/env python
"""
手動測試文檔級搜尋功能
"""

import sys
import os
import django

sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.protocol_guide.search_service import ProtocolGuideSearchService

def test_queries():
    """測試各種查詢"""
    service = ProtocolGuideSearchService()
    
    test_cases = [
        {
            'query': 'IOL 放測 SOP',
            'expected_type': 'full_document',
            'description': 'SOP 關鍵詞 - 應返回完整文檔'
        },
        {
            'query': 'UNH-IOL Broadcom',
            'expected_type': 'full_document',
            'description': '命中文檔標題 - 應返回完整文檔'
        },
        {
            'query': '如何配置網路設定',
            'expected_type': 'section',
            'description': '一般查詢 - 應返回 section + context'
        },
        {
            'query': 'Protocol 測試流程',
            'expected_type': 'full_document',
            'description': '流程關鍵詞 - 應返回完整文檔'
        },
    ]
    
    print("=" * 80)
    print("文檔級搜尋功能測試")
    print("=" * 80)
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case['query']
        expected = test_case['expected_type']
        desc = test_case['description']
        
        print(f"\n測試 {i}: {desc}")
        print(f"Query: {query}")
        print(f"Expected: {expected}")
        
        results = service.search_knowledge(query, limit=1)
        
        if not results:
            print("❌ FAIL: No results returned")
            continue
        
        result = results[0]
        result_type = result['metadata'].get('type', 'section')
        content_length = len(result['content'])
        
        print(f"Result Type: {result_type}")
        print(f"Content Length: {content_length} chars")
        print(f"Title: {result['title']}")
        
        # 驗證
        if expected == 'full_document':
            if result_type == 'full_document' and content_length > 1000:
                print("✅ PASS")
            else:
                print("❌ FAIL: Expected full document but got section")
        else:
            if result_type != 'full_document':
                print("✅ PASS")
            else:
                print("❌ FAIL: Expected section but got full document")
    
    print("\n" + "=" * 80)
    print("測試完成")
    print("=" * 80)

if __name__ == '__main__':
    test_queries()
```

**執行測試**：
```bash
docker exec ai-django python /app/test_document_level_search_manual.py
```

---

### Phase 4: Dify 整合測試 ⏱️ 預計 1-2 小時

#### 4.1 測試 Dify 外部知識庫 API

```bash
# 測試 Protocol Guide 外部知識庫 API
curl -X POST "http://localhost/api/dify/protocol-guide/search/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "IOL 放測 SOP",
    "knowledge_id": "protocol_guide_db",
    "retrieval_setting": {
      "top_k": 1,
      "score_threshold": 0.5
    }
  }'
```

**預期回應**：
```json
{
  "records": [
    {
      "content": "# UNH-IOL (Broadcom) 放測 SOP\n\n## 1. Section 1 Title\nSection 1 content...\n\n## 2. Section 2 Title\n...",
      "score": 0.89,
      "title": "UNH-IOL (Broadcom) 放測 SOP",
      "metadata": {
        "type": "full_document",
        "document_id": "doc_1",
        "section_count": 10,
        "total_length": 2345
      }
    }
  ]
}
```

**驗證點**：
- ✅ Content 長度 > 1000 字元 (完整文檔)
- ✅ Metadata type = 'full_document'
- ✅ 包含多個 sections (section_count >= 7)

#### 4.2 測試 Protocol Assistant Chat

```bash
# 測試 Protocol Assistant 聊天功能
curl -X POST "http://localhost/api/protocol-guide/chat/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "message": "請說明 IOL 放測的完整 SOP 流程",
    "conversation_id": ""
  }'
```

**預期行為**：
1. Django 接收聊天請求
2. Dify 向 Django 請求知識庫內容 (`/api/dify/protocol-guide/search/`)
3. Django 返回完整文檔內容 (2000+ 字元)
4. Dify LLM 看到完整 SOP 流程
5. Dify 生成完整的回答
6. Django 返回給 Frontend

**驗證回應**：
```json
{
  "success": true,
  "answer": "根據 UNH-IOL (Broadcom) 放測 SOP，完整流程如下：\n\n1. 前置準備...\n2. 環境配置...\n3. IOL 放測步驟...\n...",
  "conversation_id": "conv_xxx",
  "message_id": "msg_xxx",
  "response_time": 3.5,
  "metadata": {
    "retriever_resources": [
      {
        "document_name": "UNH-IOL (Broadcom) 放測 SOP",
        "score": 0.89
      }
    ]
  }
}
```

**驗證點**：
- ✅ Answer 包含完整 SOP 流程
- ✅ Metadata 顯示使用了外部知識庫
- ✅ Answer 長度 > 500 字元 (完整回答)

#### 4.3 對比測試

**測試方法**: 同樣的查詢，對比修改前後的回答

| 項目 | 修改前 | 修改後 |
|------|--------|--------|
| 查詢內容數量 | 1 個 section (332 chars) | 完整文檔 (2000+ chars) |
| AI 回答完整度 | 只提到 Section 3 內容 | 涵蓋所有步驟 |
| 是否提到前置準備 | ❌ 否 | ✅ 是 |
| 是否提到後續步驟 | ❌ 否 | ✅ 是 |
| 用戶滿意度 | 👎 不完整 | 👍 完整且有用 |

---

## 📊 成功標準

### 功能驗證
- ✅ SOP 類查詢返回完整文檔 (>1000 字元)
- ✅ 一般查詢保持 section 級搜尋
- ✅ 所有現有測試通過 (無 regression)
- ✅ 新測試套件全部通過

### 資料庫驗證
- ✅ 所有 section 都有 `document_id` 和 `document_title`
- ✅ 每個文檔有一個 `is_document_title=TRUE` 記錄
- ✅ 資料完整性：無 NULL 值（除了預期的）

### API 驗證
- ✅ Dify 外部知識庫 API 返回完整文檔
- ✅ Protocol Assistant Chat 使用完整文檔回答
- ✅ Metadata 正確標記文檔類型

### 效能驗證
- ✅ 查詢回應時間 < 5 秒
- ✅ 資料庫查詢效率 (使用索引)
- ✅ 記憶體使用合理 (不會 OOM)

---

## 🚀 部署計畫

### 開發環境部署 ⏱️ 1 天
1. 執行資料庫 migration
2. 填充現有資料
3. 部署新版 search_service.py
4. 執行所有測試
5. 驗證功能正常

### 測試環境部署 ⏱️ 1-2 天
1. 同步開發環境變更
2. 執行完整測試套件
3. 用戶驗收測試 (UAT)
4. 收集反饋

### 生產環境部署 ⏱️ 半天
1. 備份資料庫
2. 執行 migration (低峰時段)
3. 部署新程式碼
4. 監控系統狀態
5. 準備回滾方案

---

## 🔄 回滾計畫

### 如果出現問題，快速回滾步驟：

#### 1. 程式碼回滾
```bash
# 回滾到上一版本
git revert <commit_hash>
docker compose restart ai-django
```

#### 2. 資料庫回滾 (可選)
```sql
-- 移除新增欄位 (如果需要)
ALTER TABLE document_section_embeddings 
DROP COLUMN IF EXISTS document_id,
DROP COLUMN IF EXISTS document_title,
DROP COLUMN IF EXISTS is_document_title;
```

#### 3. 快速驗證
```bash
# 驗證系統恢復正常
docker exec ai-django python manage.py check
curl -X GET http://localhost/api/health/
```

---

## 📅 時間表

| Phase | 任務 | 預計時間 | 負責人 | 備註 |
|-------|------|---------|--------|------|
| Phase 1 | 資料庫結構升級 | 2-3 小時 | Backend Team | 包含驗證 |
| Phase 2 | 搜尋邏輯升級 | 4-5 小時 | Backend Team | 核心邏輯 |
| Phase 3 | 測試驗證 | 2-3 小時 | QA Team | 單元+整合測試 |
| Phase 4 | Dify 整合測試 | 1-2 小時 | Full Stack Team | 端到端測試 |
| **總計** | **全部 Phases** | **10-13 小時** | - | 約 2 個工作天 |

---

## 🎯 關鍵決策與設計理念

### 為什麼選擇這個方案？

1. **最小改動原則**
   - ✅ Frontend 完全不需要修改
   - ✅ 只修改 Backend Search Service
   - ✅ 保留現有功能，不影響其他查詢

2. **智能判斷機制**
   - ✅ 根據查詢類型動態調整
   - ✅ SOP 類查詢返回完整文檔
   - ✅ 一般查詢保持 section 級搜尋
   - ✅ 用戶無需改變使用習慣

3. **資料完整性**
   - ✅ 添加文檔層級資訊
   - ✅ 支援未來更多文檔級功能
   - ✅ 不破壞現有資料結構

4. **效能考量**
   - ✅ 使用索引優化查詢
   - ✅ 只在需要時才載入完整文檔
   - ✅ 合理的快取策略

### 替代方案比較

| 方案 | 優點 | 缺點 | 決策 |
|------|------|------|------|
| **方案 1: 智能判斷** | Frontend 不需改, 邏輯清晰 | 需要判斷邏輯 | ✅ **採用** |
| 方案 2: 用戶選擇 | 用戶可控 | 需要修改 UI, 增加複雜度 | ❌ 不採用 |
| 方案 3: 總是返回完整文檔 | 最簡單 | 效能問題, Token 浪費 | ❌ 不採用 |
| 方案 4: 多次查詢合併 | 靈活 | 複雜度高, 延遲增加 | ❌ 不採用 |

---

## 📚 相關文檔

### 已完成的相關功能
- ✅ 上下文視窗擴展功能 (`context-window-expansion-final-summary.md`)
- ✅ 向量搜尋系統 (`vector-search-guide.md`)
- ✅ Multi-Vector Search (Title 60% + Content 40%)

### 本次新增功能
- 🆕 文檔級搜尋 (Document-Level Search)
- 🆕 智能查詢分類 (Query Classification)
- 🆕 動態內容擴展 (Dynamic Context Expansion)

### 技術基礎
- PostgreSQL + pgvector
- Django ORM
- Dify External Knowledge API
- Multi-Vector Embedding (1024-dim)

---

## ✅ 核心優勢總結

### 1. **Frontend 零修改** 🎉
- Frontend 只接收 `{ answer: "..." }` 並顯示
- 所有邏輯都在 Backend + Dify 處理
- 用戶體驗無縫升級

### 2. **智能且彈性** 🧠
- SOP 查詢 → 完整文檔
- 一般查詢 → section + context
- 未來可擴展更多查詢類型

### 3. **向後兼容** 🔄
- 保留所有現有功能
- 現有測試全部通過
- 無 breaking changes

### 4. **實施簡單** ⚡
- 10-13 小時完成
- 清晰的步驟和驗證
- 完整的回滾方案

---

**📝 計畫狀態**: ✅ 已完成  
**📅 創建日期**: 2025-11-10  
**✍️ 作者**: AI Platform Team  
**🎯 下一步**: 等待審核批准後開始實施

---

## 🤔 待討論問題

1. **查詢分類邏輯**: 是否需要更精細的分類規則？
2. **文檔長度限制**: 是否需要對超長文檔進行截斷？
3. **快取策略**: 完整文檔是否需要快取？
4. **監控指標**: 需要添加哪些新的監控指標？
5. **用戶反饋**: 是否需要添加「返回完整文檔」的反饋按鈕？

---

**備註**: 本計畫專注於解決「SOP 文檔被截斷」問題，不包含 UI 層面的優化（如展開/收合、範圍指示器等），這些可作為未來的可選增強功能。
