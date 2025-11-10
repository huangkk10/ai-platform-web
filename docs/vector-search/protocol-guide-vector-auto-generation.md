# Protocol Assistant 知識庫新增資料時的向量生成分析

**分析日期**：2025-11-10  
**分析目的**：確認新增 Protocol Guide 時，向量資料是否會自動生成  
**結論**：✅ **會自動生成！而且生成兩種向量！**

---

## 🎯 快速答案

**是的！當您在 Protocol Assistant 知識庫中新增 Protocol Guide 時，系統會自動生成向量資料。**

而且，系統會生成 **兩種向量**：

1. **整篇文檔向量**（舊系統）：儲存在 `document_embeddings` 表
2. **段落向量**（新系統）：儲存在 `protocol_guide_sections` 和 `protocol_section_vectors_multi` 表

---

## 🔍 詳細分析

### 📋 系統架構

Protocol Guide 的向量生成使用了 **雙層架構**：

```
用戶新增 Protocol Guide
        ↓
ProtocolGuideViewSet (ViewSet 層)
        ↓
判斷：Library 是否可用？
        ↓
    ┌───YES───┐         ┌───NO (Fallback)───┐
    ↓                   ↓
ProtocolGuideViewSetManager   ViewSet 內建邏輯
(Library 層)                 (直接處理)
    ↓                        ↓
perform_create()         perform_create()
    ↓                        ↓
自動生成兩種向量           自動生成兩種向量
```

### 1️⃣ **ViewSet 配置確認**

**檔案**：`backend/api/views/viewsets/knowledge_viewsets.py`（第 878-912 行）

```python
class ProtocolGuideViewSet(
    LibraryManagerMixin,        # ✅ Library 管理
    FallbackLogicMixin,         # ✅ 降級邏輯
    VectorManagementMixin,      # ✅ 向量管理
    viewsets.ModelViewSet
):
    """Protocol Guide ViewSet - 使用 Mixins 重構"""
    
    # 🎯 配置 Library Manager
    library_config = {
        'library_available_flag': 'PROTOCOL_GUIDE_LIBRARY_AVAILABLE',
        'manager_class': 'ProtocolGuideViewSetManager',
        'library_name': 'Protocol Guide Library',
        'manager_attribute': 'viewset_manager'
    }
    
    # 🎯 配置 Vector Management
    vector_config = {
        'source_table': 'protocol_guide',
        'use_1024_table': True,  # ✅ 使用 1024 維向量
        'content_fields': ['title', 'content', 'protocol_name', 'version'],
        'vector_enabled': True   # ✅ 啟用向量生成
    }
```

**關鍵配置**：
- ✅ `vector_enabled: True` - 向量生成已啟用
- ✅ 使用三個 Mixins，確保向量自動管理
- ✅ Library 可用標誌：`PROTOCOL_GUIDE_LIBRARY_AVAILABLE = True`

---

### 2️⃣ **Library Manager 實現確認**

**檔案**：`library/protocol_guide/viewset_manager.py`（第 46-81 行）

```python
class ProtocolGuideViewSetManager(BaseKnowledgeBaseViewSetManager):
    """Protocol Guide ViewSet 管理器"""
    
    def perform_create(self, serializer):
        """
        創建 Protocol Guide 時自動生成段落向量
        
        流程：
        1. 保存實例到資料庫
        2. 生成整篇文檔向量（舊系統） ✅
        3. 生成段落向量（新系統） ✅
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 1. 保存實例
        instance = serializer.save()
        
        # 2. 生成整篇文檔向量（舊系統）
        try:
            self.generate_vector_for_instance(instance, action='create')
            logger.info(f"✅ Protocol Guide {instance.id} 整篇文檔向量生成成功")
        except Exception as e:
            logger.error(f"❌ 整篇文檔向量生成失敗: {str(e)}")
        
        # 3. 生成段落向量（新系統）
        try:
            from library.common.knowledge_base.section_vectorization_service import SectionVectorizationService
            
            vectorization_service = SectionVectorizationService()
            section_count = vectorization_service.vectorize_document_sections(
                source_table='protocol_guide',
                source_id=instance.id,
                markdown_content=instance.content,
                metadata={'title': instance.title}
            )
            logger.info(f"✅ Protocol Guide {instance.id} 段落向量生成成功 ({section_count} 個段落)")
        except Exception as e:
            logger.error(f"❌ 段落向量生成失敗: {str(e)}")
        
        return instance
```

**關鍵實現**：
- ✅ **步驟 2**：調用 `generate_vector_for_instance()` 生成整篇向量
- ✅ **步驟 3**：調用 `SectionVectorizationService` 生成段落向量
- ✅ **錯誤處理**：即使向量生成失敗，資料仍會儲存（不影響主流程）

---

### 3️⃣ **Fallback 機制確認**

**如果 Library 不可用**，ViewSet 也有備用邏輯（第 958-991 行）：

```python
def perform_create(self, serializer):
    """建立新的 Protocol Guide + 自動向量生成（整篇 + 段落）"""
    import logging
    logger = logging.getLogger(__name__)
    
    if self.has_manager():
        # 如果 Manager 可用，使用 Manager（已包含段落向量生成）
        instance = self._manager.perform_create(serializer)
    else:
        # Fallback: 手動實現
        instance = serializer.save()
        
        # 1. 生成整篇文檔向量（舊系統）
        try:
            self.generate_vector_for_instance(instance, action='create')
            logger.info(f"✅ Protocol Guide {instance.id} 整篇向量生成成功")
        except Exception as e:
            logger.error(f"❌ 整篇向量生成失敗: {str(e)}")
        
        # 2. 生成段落向量（新系統）
        try:
            from library.common.knowledge_base.section_vectorization_service import SectionVectorizationService
            vectorization_service = SectionVectorizationService()
            result = vectorization_service.vectorize_document_sections(
                source_table='protocol_guide',
                source_id=instance.id,
                markdown_content=instance.content,
                document_title=instance.title
            )
            if result.get('success'):
                logger.info(f"✅ Protocol Guide {instance.id} 段落向量生成成功 ({result.get('vectorized_count')} 個段落)")
        except Exception as e:
            logger.error(f"❌ 段落向量生成失敗: {str(e)}")
    
    return instance
```

**備用機制**：
- ✅ **雙重保障**：即使 Library 失敗，ViewSet 內建邏輯也會生成向量
- ✅ **完整流程**：Fallback 也包含整篇 + 段落兩種向量生成

---

## 📊 生成的向量資料結構

### 向量 1：整篇文檔向量（舊系統）

**儲存表**：`document_embeddings`

```sql
-- 查詢範例
SELECT 
    id,
    source_table,
    source_id,
    LENGTH(text_content) as content_length,
    vector_dims(embedding) as dimension,
    created_at
FROM document_embeddings
WHERE source_table = 'protocol_guide'
  AND source_id = 123;  -- 您的 Protocol Guide ID
```

**預期結果**：
```
id | source_table   | source_id | content_length | dimension | created_at
----+----------------+-----------+----------------+-----------+------------
456| protocol_guide | 123       | 2500           | 1024      | 2025-11-10
```

**用途**：
- 舊版向量搜尋（向後相容）
- 整篇文檔的語義表示

---

### 向量 2：段落向量（新系統）

**儲存表 1**：`protocol_guide_sections`（段落內容）

```sql
-- 查詢段落
SELECT 
    id,
    document_id,
    heading,
    heading_level,
    content_preview
FROM protocol_guide_sections
WHERE document_id = 123  -- 您的 Protocol Guide ID
ORDER BY heading_level, id;
```

**預期結果**：
```
id  | document_id | heading           | heading_level | content_preview
----+-------------+-------------------+---------------+-----------------
501 | 123         | # IOL 測試流程     | 1             | IOL（Interop...
502 | 123         | ## 1. 環境準備     | 2             | 在開始測試前...
503 | 123         | ### 1.1 硬體需求  | 3             | - PC 一台...
```

**儲存表 2**：`protocol_section_vectors_multi`（段落向量）

```sql
-- 查詢段落向量
SELECT 
    id,
    section_id,
    vector_index,
    vector_dims(embedding) as dimension,
    created_at
FROM protocol_section_vectors_multi
WHERE section_id IN (
    SELECT id FROM protocol_guide_sections WHERE document_id = 123
);
```

**預期結果**：
```
id   | section_id | vector_index | dimension | created_at
-----+------------+--------------+-----------+------------
1001 | 501        | 0            | 1024      | 2025-11-10
1002 | 502        | 0            | 1024      | 2025-11-10
1003 | 503        | 0            | 1024      | 2025-11-10
```

**用途**：
- **文檔級搜尋**：組裝完整文檔
- **Section 級搜尋**：精確定位段落
- **多向量支援**：大型段落可分割成多個向量

---

## 🧪 驗證方法

### 方法 1：透過前端新增資料並檢查日誌

```bash
# 1. 在前端新增一個 Protocol Guide
# 訪問：http://localhost/knowledge/protocol-log
# 點擊「新增 Protocol Guide」

# 2. 立即查看 Django 日誌
docker logs ai-django | grep "Protocol Guide" | tail -20
```

**預期看到的日誌**：
```
✅ Protocol Guide 123 整篇文檔向量生成成功
✅ Protocol Guide 123 段落向量生成成功 (8 個段落)
```

---

### 方法 2：直接查詢資料庫

```bash
# 進入 PostgreSQL
docker exec -it postgres_db psql -U postgres -d ai_platform

# 查詢最新的 Protocol Guide
SELECT id, title, created_at 
FROM protocol_guide 
ORDER BY created_at DESC 
LIMIT 1;

# 假設 ID 是 123，檢查整篇向量
SELECT COUNT(*) as count
FROM document_embeddings
WHERE source_table = 'protocol_guide' AND source_id = 123;

# 檢查段落
SELECT COUNT(*) as section_count
FROM protocol_guide_sections
WHERE document_id = 123;

# 檢查段落向量
SELECT COUNT(*) as vector_count
FROM protocol_section_vectors_multi psvm
JOIN protocol_guide_sections pgs ON psvm.section_id = pgs.id
WHERE pgs.document_id = 123;
```

**預期結果**：
```
-- 整篇向量
count
------
  1

-- 段落數量（假設有 8 個標題）
section_count
-------------
         8

-- 段落向量數量（與段落數量相同）
vector_count
------------
        8
```

---

### 方法 3：使用測試腳本

創建一個簡單的測試腳本：

```bash
#!/bin/bash
# test_vector_generation.sh

echo "================================================"
echo "Protocol Guide 向量生成測試"
echo "================================================"
echo ""

# 測試：新增 Protocol Guide 後檢查向量
PROTOCOL_ID=$1

if [ -z "$PROTOCOL_ID" ]; then
    echo "❌ 請提供 Protocol Guide ID"
    echo "用法: ./test_vector_generation.sh <protocol_id>"
    exit 1
fi

echo "檢查 Protocol Guide ID: $PROTOCOL_ID"
echo ""

# 1. 檢查整篇向量
echo "1️⃣ 檢查整篇文檔向量..."
FULL_VECTOR=$(docker exec postgres_db psql -U postgres -d ai_platform -t -c \
  "SELECT COUNT(*) FROM document_embeddings WHERE source_table='protocol_guide' AND source_id=$PROTOCOL_ID;")

if [ "$FULL_VECTOR" -gt 0 ]; then
    echo "✅ 整篇向量存在 (數量: $FULL_VECTOR)"
else
    echo "❌ 整篇向量不存在"
fi
echo ""

# 2. 檢查段落
echo "2️⃣ 檢查段落資料..."
SECTION_COUNT=$(docker exec postgres_db psql -U postgres -d ai_platform -t -c \
  "SELECT COUNT(*) FROM protocol_guide_sections WHERE document_id=$PROTOCOL_ID;")

if [ "$SECTION_COUNT" -gt 0 ]; then
    echo "✅ 段落資料存在 (數量: $SECTION_COUNT)"
else
    echo "❌ 段落資料不存在"
fi
echo ""

# 3. 檢查段落向量
echo "3️⃣ 檢查段落向量..."
SECTION_VECTOR=$(docker exec postgres_db psql -U postgres -d ai_platform -t -c \
  "SELECT COUNT(*) FROM protocol_section_vectors_multi psvm 
   JOIN protocol_guide_sections pgs ON psvm.section_id = pgs.id 
   WHERE pgs.document_id=$PROTOCOL_ID;")

if [ "$SECTION_VECTOR" -gt 0 ]; then
    echo "✅ 段落向量存在 (數量: $SECTION_VECTOR)"
else
    echo "❌ 段落向量不存在"
fi
echo ""

# 總結
echo "================================================"
echo "測試總結"
echo "================================================"
if [ "$FULL_VECTOR" -gt 0 ] && [ "$SECTION_COUNT" -gt 0 ] && [ "$SECTION_VECTOR" -gt 0 ]; then
    echo "🎉 所有向量都已正確生成！"
    exit 0
else
    echo "⚠️  部分向量缺失，請檢查日誌"
    exit 1
fi
```

**使用方法**：
```bash
chmod +x test_vector_generation.sh
./test_vector_generation.sh 123  # 替換成實際的 Protocol Guide ID
```

---

## ❓ 常見問題

### Q1：如果向量生成失敗會怎樣？

**答**：資料仍會儲存到資料庫，但會在日誌中記錄錯誤。

```python
try:
    self.generate_vector_for_instance(instance, action='create')
    logger.info(f"✅ Protocol Guide {instance.id} 整篇文檔向量生成成功")
except Exception as e:
    logger.error(f"❌ 整篇文檔向量生成失敗: {str(e)}")
    # ⚠️ 注意：不會拋出異常，資料會保留
```

**查看錯誤**：
```bash
docker logs ai-django | grep "向量生成失敗" | tail -10
```

---

### Q2：舊資料沒有向量怎麼辦？

**答**：可以使用批量生成腳本補救。

參考：`/docs/vector-search/ai-vector-search-guide.md` 中的「場景 1：舊資料沒有向量」

---

### Q3：如何驗證向量是否正確？

**答**：測試搜尋功能。

```bash
# 測試外部知識庫 API
curl -X POST "http://localhost/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "protocol_guide_db",
    "query": "您新增的 Protocol Guide 標題",
    "retrieval_setting": {"top_k": 3, "score_threshold": 0.5}
  }' | python3 -m json.tool
```

**預期**：應該能搜尋到您新增的資料。

---

### Q4：Library 是否可用？

**答**：是的！確認方法：

```bash
# 檢查 Library 標誌
grep "PROTOCOL_GUIDE_LIBRARY_AVAILABLE" library/protocol_guide/__init__.py
```

**預期結果**：
```python
PROTOCOL_GUIDE_LIBRARY_AVAILABLE = True
```

---

## 📚 相關文檔

- **向量生成完整指南**：`/docs/vector-search/ai-vector-search-guide.md`
- **文檔級搜尋架構**：`/docs/architecture/document-level-search-architecture.md`
- **Protocol Guide API 架構**：`/docs/features/protocol-guide-api-architecture.md`

---

## 🎯 結論

**✅ 是的！當您在 Protocol Assistant 知識庫中新增 Protocol Guide 時：**

1. **系統會自動生成整篇文檔向量**（儲存在 `document_embeddings`）
2. **系統會自動生成段落向量**（儲存在 `protocol_guide_sections` 和 `protocol_section_vectors_multi`）
3. **雙重保障機制**：Library Manager + ViewSet Fallback
4. **錯誤不影響主流程**：即使向量生成失敗，資料仍會儲存

**您不需要手動生成向量！一切都是自動的！**

---

**作者**：AI Platform Team  
**更新日期**：2025-11-10  
**版本**：v1.0  
**狀態**：✅ 已確認
