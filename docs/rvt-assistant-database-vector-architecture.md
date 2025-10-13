# RVT Assistant 資料庫與向量系統運作原理

> **文檔版本**: v1.0  
> **建立日期**: 2025-10-13  
> **適用對象**: AI 助手、系統開發者、運維人員  

## 🎯 概述

本文檔詳細說明 RVT Assistant 系統中 User Guide 的 CRUD 操作如何與資料庫和向量資料庫進行同步，提供完整的技術架構和運作流程。

## 🏗️ 系統架構

### 核心組件

1. **資料庫層 (PostgreSQL)**
   - `rvt_guide` 表：儲存 RVT Guide 基本資料
   - `content_images` 表：儲存關聯的圖片資訊

2. **向量資料庫層 (PostgreSQL + pgvector)**
   - `document_embeddings_1024` 表：儲存 1024 維向量（主要）
   - `document_embeddings` 表：儲存 768 維向量（備用）

3. **應用層組件**
   - `RVTGuideViewSet`：API 端點處理
   - `RVTGuideViewSetManager`：業務邏輯管理
   - `RVTGuideVectorService`：向量處理服務
   - `OpenSourceEmbeddingService`：向量生成服務

## 📊 資料庫結構

### RVT Guide 主表
```sql
-- rvt_guide 表結構
CREATE TABLE rvt_guide (
    id SERIAL PRIMARY KEY,
    title VARCHAR(300) NOT NULL,           -- 文檔標題
    content TEXT NOT NULL,                 -- 文檔內容
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 向量資料表
```sql
-- document_embeddings_1024 表結構 (1024維向量 - 主要)
CREATE TABLE document_embeddings_1024 (
    id SERIAL PRIMARY KEY,
    source_table VARCHAR(100) NOT NULL,    -- 來源表名 ('rvt_guide')
    source_id INTEGER NOT NULL,            -- 對應的 rvt_guide.id
    text_content TEXT NOT NULL,            -- 向量化的文本內容
    embedding vector(1024),                -- 1024維向量
    metadata JSONB,                        -- 額外元數據
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content_hash VARCHAR(64),              -- 內容雜湊值
    
    UNIQUE(source_table, source_id)        -- 確保一對一關係
);
```

### 圖片關聯表
```sql
-- content_images 表結構
CREATE TABLE content_images (
    id SERIAL PRIMARY KEY,
    content_type VARCHAR(50),              -- 'rvt-guide'
    content_id INTEGER,                    -- 對應的 rvt_guide.id
    title VARCHAR(255),                    -- 圖片標題
    description TEXT,                      -- 圖片描述
    filename VARCHAR(255),                 -- 檔案名稱
    file_data BYTEA,                      -- 圖片二進位資料
    display_order INTEGER DEFAULT 0,      -- 顯示順序
    is_primary BOOLEAN DEFAULT FALSE,     -- 是否為主要圖片
    is_active BOOLEAN DEFAULT TRUE,       -- 是否啟用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔄 CRUD 操作流程

### 1. 新增 (CREATE) 操作

#### 流程圖
```
用戶提交新 User Guide
         ↓
RVTGuideViewSet.perform_create()
         ↓
RVTGuideViewSetManager.perform_create()
         ↓
serializer.save() → 寫入 rvt_guide 表
         ↓
generate_vector_for_guide(action='create')
         ↓
RVTGuideVectorService.generate_and_store_vector()
         ↓
格式化內容 + 生成向量 + 寫入 document_embeddings_1024
```

#### 程式碼實現
```python
# 1. ViewSet 處理
def perform_create(self, serializer):
    """建立新的 RVT Guide"""
    if self.viewset_manager:
        return self.viewset_manager.perform_create(serializer)

# 2. ViewSetManager 邏輯
def perform_create(self, serializer):
    instance = serializer.save()  # 寫入主表
    self.generate_vector_for_guide(instance, action='create')  # 生成向量
    return instance

# 3. 向量生成
def generate_vector_for_guide(self, instance, action='create'):
    vector_service = RVTGuideVectorService()
    success = vector_service.generate_and_store_vector(instance, action)
```

#### 向量內容格式化
```python
def _format_content_for_embedding(self, instance):
    content_parts = []
    
    # 標題
    if instance.title:
        content_parts.append(f"標題: {instance.title}")
    
    # 內容
    if instance.content:
        content_parts.append(f"內容: {instance.content}")
    
    # 圖片摘要 (🆕 自動包含)
    if hasattr(instance, 'get_images_summary'):
        images_summary = instance.get_images_summary()
        if images_summary:
            content_parts.append(images_summary)
    
    return "\n".join(content_parts)
```

### 2. 更新 (UPDATE) 操作

#### 流程圖
```
用戶更新 User Guide
         ↓
RVTGuideViewSet.perform_update()
         ↓
RVTGuideViewSetManager.perform_update()
         ↓
serializer.save() → 更新 rvt_guide 表
         ↓
generate_vector_for_guide(action='update')
         ↓
RVTGuideVectorService.generate_and_store_vector()
         ↓
重新生成向量 + 更新 document_embeddings_1024
```

#### 程式碼實現
```python
# 1. ViewSet 處理
def perform_update(self, serializer):
    """更新現有的 RVT Guide"""
    if self.viewset_manager:
        return self.viewset_manager.perform_update(serializer)

# 2. 向量服務處理
def generate_and_store_vector(self, instance, action='create'):
    # 格式化內容
    content = self._format_content_for_embedding(instance)
    
    # 生成並儲存向量 (UPSERT 邏輯)
    success = self.embedding_service.store_document_embedding(
        source_table='rvt_guide',
        source_id=instance.id,
        content=content,
        use_1024_table=True
    )
```

#### 圖片更新觸發向量重建
```python
# 當圖片被新增/修改時，自動更新向量
def _update_guide_vectors(self, rvt_guide):
    """圖片變更時更新 RVT Guide 的向量資料"""
    vector_service = RVTGuideVectorService()
    vector_service.generate_and_store_vector(rvt_guide, action='update')
```

### 3. 刪除 (DELETE) 操作

#### 流程圖
```
用戶刪除 User Guide
         ↓
RVTGuideViewSet.perform_destroy()
         ↓
RVTGuideViewSetManager.perform_destroy()
         ↓
vector_service.delete_vector() → 刪除向量資料
         ↓
instance.delete() → 刪除主表資料
         ↓
級聯刪除關聯圖片 (content_images)
```

#### 程式碼實現
```python
def perform_destroy(self, instance):
    """刪除 RVT Guide 時同時刪除對應的向量資料"""
    try:
        # 1. 先刪除向量資料
        vector_service = RVTGuideVectorService()
        vector_service.delete_vector(instance)
        
        # 2. 刪除主表資料
        instance.delete()  # 會級聯刪除相關圖片
        
    except Exception as e:
        logger.error(f"刪除失敗: {str(e)}")

# 向量刪除實現
def delete_vector(self, instance):
    # 刪除 1024 維向量
    success_1024 = self.embedding_service.delete_document_embedding(
        source_table='rvt_guide',
        source_id=instance.id,
        use_1024_table=True
    )
    
    # 刪除 768 維向量 (備用)
    success_768 = self.embedding_service.delete_document_embedding(
        source_table='rvt_guide',
        source_id=instance.id,
        use_1024_table=False
    )
```

### 4. 查詢 (READ) 操作

#### 傳統查詢 vs 向量查詢

**傳統查詢** (用於 UI 列表顯示)
```python
# 基於關鍵字的搜索
queryset = RVTGuide.objects.filter(
    Q(title__icontains=search) |
    Q(content__icontains=search)
).order_by('-created_at')
```

**向量查詢** (用於 AI 智能搜索)
```python
# 基於語義的向量搜索
def search_rvt_guide_with_vectors(query: str, limit: int = 5):
    service = get_embedding_service()
    
    # 1. 生成查詢向量
    query_embedding = service.generate_embedding(query)
    
    # 2. 向量相似度搜索
    vector_results = service.search_similar_documents(
        query=query,
        source_table='rvt_guide',
        limit=limit,
        threshold=0.3,
        use_1024_table=True
    )
    
    # 3. 獲取完整資料
    return _get_rvt_guide_results(vector_results)
```

## 🚀 批量操作和定時任務

### 批量向量生成
```python
# Django 管理命令
python manage.py generate_rvt_embeddings --force --batch-size=10
```

### 重建所有向量
```python
# 程式化重建
vector_service = RVTGuideVectorService()
result = vector_service.rebuild_all_vectors()

# 結果統計
{
    'total': 50,
    'success': 48,
    'failed': 2,
    'errors': ['ID 10: 內容為空', 'ID 25: 向量生成失敗']
}
```

### Celery 定時任務 (未來擴展)
```python
# 定時重建向量 (預留架構)
@periodic_task(run_every=crontab(hour=3, minute=0))
def daily_rvt_guide_vector_rebuild():
    """每日凌晨重建 RVT Guide 向量"""
    vector_service = RVTGuideVectorService()
    return vector_service.rebuild_all_vectors()
```

## 🔧 向量模型配置

### 支援的模型類型
```python
MODEL_CONFIGS = {
    'ultra_high': {
        'name': 'intfloat/multilingual-e5-large',
        'dimension': 1024,
        'description': '超高精準度多語言模型 (預設)'
    },
    'standard': {
        'name': 'paraphrase-multilingual-mpnet-base-v2',
        'dimension': 768,
        'description': '標準多語言模型'
    },
    'lightweight': {
        'name': 'paraphrase-multilingual-MiniLM-L12-v2',
        'dimension': 384,
        'description': '輕量級多語言模型'
    }
}
```

### 向量搜索配置
```python
# 搜索參數
{
    'threshold': 0.3,      # 相似度閾值 (0.0-1.0)
    'limit': 5,            # 返回結果數量
    'use_1024_table': True # 使用 1024 維表格
}

# SQL 向量搜索 (PostgreSQL + pgvector)
SELECT 
    source_id,
    1 - (embedding <=> %s) as similarity_score
FROM document_embeddings_1024
WHERE source_table = 'rvt_guide'
ORDER BY embedding <=> %s
LIMIT 5
```

## 📈 效能監控

### 關鍵指標
```python
# 向量化覆蓋率
vectorization_coverage = (
    向量表中的記錄數 / 主表中的記錄數
) * 100

# 搜索響應時間
search_performance = {
    'vector_search': '< 100ms',  # 向量搜索
    'vector_generation': '< 2s',   # 向量生成
    'batch_processing': '~5 docs/sec'  # 批量處理
}
```

### 日誌監控
```python
# 成功日誌
logger.info(f"✅ 成功為 RVT Guide 生成向量 (create): ID {instance.id}")

# 錯誤日誌
logger.error(f"❌ RVT Guide 向量生成失敗 (update): ID {instance.id}")

# 統計日誌
logger.info(f"批量向量生成完成: 成功 {success_count}/{total_count}")
```

## 🛡️ 錯誤處理機制

### 1. 向量生成失敗
```python
try:
    success = vector_service.generate_and_store_vector(instance, action)
    if not success:
        # 記錄失敗但不阻斷主流程
        logger.error(f"向量生成失敗: ID {instance.id}")
except Exception as e:
    # 異常處理，確保 CRUD 操作正常完成
    logger.error(f"向量生成異常: {str(e)}")
```

### 2. 備用機制
```python
# 如果 library 不可用，使用備用實現
if self.viewset_manager:
    return self.viewset_manager.perform_create(serializer)
else:
    # 備用實現：只處理資料庫，跳過向量
    return serializer.save()
```

### 3. 向量搜索降級
```python
# 向量搜索失敗時降級為傳統搜索
try:
    # 嘗試向量搜索
    return search_rvt_guide_with_vectors(query)
except Exception:
    # 降級為傳統關鍵字搜索
    return RVTGuide.objects.filter(title__icontains=query)
```

## 🔍 故障排除

### 常見問題

1. **向量未生成**
   ```bash
   # 檢查向量表是否有資料
   docker exec postgres_db psql -U postgres -d ai_platform -c \
   "SELECT COUNT(*) FROM document_embeddings_1024 WHERE source_table='rvt_guide';"
   
   # 手動重建向量
   docker exec ai-django python manage.py generate_rvt_embeddings --force
   ```

2. **搜索結果不準確**
   ```python
   # 調整相似度閾值
   threshold = 0.5  # 提高閾值獲得更精準結果
   
   # 檢查向量模型類型
   service = get_embedding_service('ultra_high')  # 使用最高精度模型
   ```

3. **效能問題**
   ```sql
   -- 檢查索引使用情況
   EXPLAIN ANALYZE 
   SELECT * FROM document_embeddings_1024 
   WHERE source_table = 'rvt_guide' 
   ORDER BY embedding <=> '[...]' LIMIT 5;
   ```

### 監控腳本
```bash
#!/bin/bash
# 向量資料庫健康檢查

echo "=== RVT Assistant 向量資料庫狀態 ==="

# 1. 檢查主表記錄數
MAIN_COUNT=$(docker exec postgres_db psql -U postgres -d ai_platform -t -c \
"SELECT COUNT(*) FROM rvt_guide;")

# 2. 檢查向量表記錄數
VECTOR_COUNT=$(docker exec postgres_db psql -U postgres -d ai_platform -t -c \
"SELECT COUNT(*) FROM document_embeddings_1024 WHERE source_table='rvt_guide';")

# 3. 計算覆蓋率
COVERAGE=$(echo "scale=2; $VECTOR_COUNT * 100 / $MAIN_COUNT" | bc)

echo "主表記錄數: $MAIN_COUNT"
echo "向量表記錄數: $VECTOR_COUNT" 
echo "向量化覆蓋率: $COVERAGE%"

if (( $(echo "$COVERAGE < 80" | bc -l) )); then
    echo "⚠️  向量化覆蓋率偏低，建議重建向量"
else
    echo "✅ 向量化狀態良好"
fi
```

## 📚 相關文檔

- [向量搜索系統指南](/docs/vector-search-guide.md)
- [AI 向量搜索操作指南](/docs/ai-vector-search-guide.md)
- [Celery 定時任務架構](/docs/celery-beat-architecture-guide.md)
- [API 集成指南](/docs/guide/api-integration.md)

## 🏷️ 文檔標籤

- `#rvt-assistant` `#vector-database` `#postgresql` `#pgvector`
- `#crud-operations` `#django` `#embedding` `#search`
- `#ai-platform` `#architecture` `#documentation`

---

**維護者**: AI Platform Team  
**最後更新**: 2025-10-13  
**狀態**: ✅ 完整且可用