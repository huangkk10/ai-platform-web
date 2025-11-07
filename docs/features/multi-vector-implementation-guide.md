# 方案 A：多向量方法實施指南

**實施日期**：2025-11-06  
**實施者**：開發團隊  
**預估時間**：12.5 小時（開發 8h + 測試 4h + 遷移 0.5h）

---

## 📋 實施前檢查清單

### ✅ 準備工作

- [ ] **備份資料庫**（必須！）
- [ ] **確認開發環境**（Docker 容器運行正常）
- [ ] **通知相關人員**（系統將短暫停機）
- [ ] **準備回滾計劃**（如果出現問題）
- [ ] **建立測試環境**（先在測試環境驗證）

### 📊 當前狀態確認

```bash
# 1. 確認當前資料量
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT source_table, COUNT(*) as count 
FROM document_embeddings 
GROUP BY source_table 
ORDER BY source_table;
"

# 預期結果：
#   source_table  | count 
# ----------------+-------
#  protocol_guide |     5
#  rvt_guide      |     2

# 2. 確認容器狀態
docker compose ps

# 3. 確認磁碟空間
df -h
```

---

## 🔧 Phase 1：資料庫結構修改（預計 30 分鐘）

### Step 1.1：備份現有資料庫（5 分鐘）

```bash
# 創建備份目錄
mkdir -p /home/user/codes/ai-platform-web/backups/multi-vector-migration

# 備份整個資料庫
docker exec postgres_db pg_dump -U postgres ai_platform > \
  /home/user/codes/ai-platform-web/backups/multi-vector-migration/backup_$(date +%Y%m%d_%H%M%S).sql

# 備份向量表（額外保險）
docker exec postgres_db pg_dump -U postgres -t document_embeddings ai_platform > \
  /home/user/codes/ai-platform-web/backups/multi-vector-migration/document_embeddings_backup_$(date +%Y%m%d_%H%M%S).sql

# 確認備份檔案大小
ls -lh /home/user/codes/ai-platform-web/backups/multi-vector-migration/
```

### Step 1.2：創建表結構修改腳本（10 分鐘）

創建 SQL 腳本：`scripts/migrate_to_multi_vector.sql`

```sql
-- ==========================================
-- 多向量表結構遷移腳本
-- 日期：2025-11-06
-- 用途：為 document_embeddings 添加標題和內容向量欄位
-- ==========================================

BEGIN;

-- Step 1: 檢查當前表結構
\d document_embeddings

-- Step 2: 添加新欄位（允許 NULL）
ALTER TABLE document_embeddings 
    ADD COLUMN IF NOT EXISTS title_embedding vector(1024),
    ADD COLUMN IF NOT EXISTS content_embedding vector(1024);

-- Step 3: 確認欄位已添加
\d document_embeddings

-- Step 4: 創建標題向量索引
CREATE INDEX IF NOT EXISTS idx_document_embeddings_title_vector 
    ON document_embeddings 
    USING ivfflat (title_embedding vector_cosine_ops) 
    WITH (lists = 100);

-- Step 5: 創建內容向量索引
CREATE INDEX IF NOT EXISTS idx_document_embeddings_content_vector 
    ON document_embeddings 
    USING ivfflat (content_embedding vector_cosine_ops) 
    WITH (lists = 100);

-- Step 6: 確認索引已創建
\di idx_document_embeddings_*

-- Step 7: 查看表統計
SELECT 
    count(*) as total_records,
    count(embedding) as old_vectors,
    count(title_embedding) as title_vectors,
    count(content_embedding) as content_vectors
FROM document_embeddings;

COMMIT;

-- 回滾指令（如果需要）
-- BEGIN;
-- DROP INDEX IF EXISTS idx_document_embeddings_content_vector;
-- DROP INDEX IF EXISTS idx_document_embeddings_title_vector;
-- ALTER TABLE document_embeddings DROP COLUMN IF EXISTS content_embedding;
-- ALTER TABLE document_embeddings DROP COLUMN IF EXISTS title_embedding;
-- COMMIT;
```

### Step 1.3：執行資料庫遷移（15 分鐘）

```bash
# 執行遷移腳本
docker exec -i postgres_db psql -U postgres -d ai_platform < scripts/migrate_to_multi_vector.sql

# 驗證結果
docker exec postgres_db psql -U postgres -d ai_platform -c "\d document_embeddings"

# 檢查索引
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE tablename = 'document_embeddings';
"
```

---

## 💻 Phase 2：程式碼修改（預計 4 小時）

### Step 2.1：修改 embedding_service.py（60 分鐘）

**檔案**：`backend/api/services/embedding_service.py`

#### 2.1.1 添加多向量生成方法

在 `OpenSourceEmbeddingService` 類別中添加：

```python
def store_document_embeddings_multi(
    self, 
    source_table: str, 
    source_id: int, 
    title: str,
    content: str,
    use_1024_table: bool = True
) -> bool:
    """
    為文檔生成並存儲標題和內容向量
    
    Args:
        source_table: 來源表名
        source_id: 來源記錄 ID
        title: 標題文本
        content: 內容文本
        use_1024_table: 是否使用 1024 維表（固定為 True）
    
    Returns:
        bool: 是否成功
    """
    try:
        # 生成標題向量
        logger.info(f"生成標題向量: {source_table} ID {source_id}")
        title_embedding = self.generate_embedding(title)
        
        # 生成內容向量
        logger.info(f"生成內容向量: {source_table} ID {source_id}")
        content_embedding = self.generate_embedding(content)
        
        # 計算內容雜湊（用於檢測變更）
        combined_content = f"{title}|{content}"
        content_hash = hashlib.sha256(combined_content.encode()).hexdigest()
        
        # 存儲到資料庫
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO document_embeddings 
                    (source_table, source_id, text_content, content_hash, 
                     title_embedding, content_embedding, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source_table, source_id) 
                DO UPDATE SET
                    text_content = EXCLUDED.text_content,
                    content_hash = EXCLUDED.content_hash,
                    title_embedding = EXCLUDED.title_embedding,
                    content_embedding = EXCLUDED.content_embedding,
                    embedding = EXCLUDED.embedding,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                [
                    source_table,
                    source_id,
                    combined_content[:1000],  # 儲存前 1000 字元
                    content_hash,
                    json.dumps(title_embedding),
                    json.dumps(content_embedding),
                    json.dumps(title_embedding),  # 保留舊的 embedding 欄位（向後兼容）
                ]
            )
        
        logger.info(f"✅ 多向量存儲成功: {source_table} ID {source_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ 多向量存儲失敗: {source_table} ID {source_id}, 錯誤: {str(e)}")
        return False
```

#### 2.1.2 添加多向量搜索方法

```python
def search_similar_documents_multi(
    self, 
    query: str, 
    source_table: str = None, 
    limit: int = 5, 
    threshold: float = 0.0,
    title_weight: float = 0.6,
    content_weight: float = 0.4
) -> List[dict]:
    """
    使用多向量方法搜索相似文檔
    
    Args:
        query: 查詢文本
        source_table: 限制搜索的來源表
        limit: 返回結果數量
        threshold: 相似度閾值
        title_weight: 標題權重 (0.0 ~ 1.0)
        content_weight: 內容權重 (0.0 ~ 1.0)
    
    Returns:
        相似文檔列表（包含 title_score, content_score, final_score）
    """
    try:
        # 生成查詢向量
        query_embedding = self.generate_embedding(query)
        embedding_json = json.dumps(query_embedding)
        
        # 構建 SQL 查詢
        sql_parts = []
        params = []
        
        if source_table:
            sql_parts.append("WHERE de.source_table = %s")
            params.append(source_table)
        
        sql = f"""
            SELECT 
                de.source_table,
                de.source_id,
                -- 標題相似度
                1 - (de.title_embedding <=> %s::vector) as title_score,
                -- 內容相似度
                1 - (de.content_embedding <=> %s::vector) as content_score,
                -- 加權最終分數
                (%s * (1 - (de.title_embedding <=> %s::vector))) + 
                (%s * (1 - (de.content_embedding <=> %s::vector))) as final_score,
                de.created_at,
                de.updated_at
            FROM document_embeddings de
            {' '.join(sql_parts)}
            ORDER BY final_score DESC
            LIMIT %s
        """
        
        # 準備參數
        query_params = [
            embedding_json,  # title_score
            embedding_json,  # content_score
            title_weight,    # title weight
            embedding_json,  # title weight calculation
            content_weight,  # content weight
            embedding_json,  # content weight calculation
        ]
        params = query_params + params + [limit]
        
        results = []
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            
            for row in cursor.fetchall():
                (source_table_name, source_id, title_score, content_score, 
                 final_score, created_at, updated_at) = row
                
                # 過濾低於閾值的結果
                if final_score >= threshold:
                    # 判斷匹配類型
                    if title_score > content_score * 1.5:
                        match_type = 'title_primary'
                    elif content_score > title_score * 1.5:
                        match_type = 'content_primary'
                    else:
                        match_type = 'balanced'
                    
                    results.append({
                        'source_table': source_table_name,
                        'source_id': source_id,
                        'title_score': float(title_score),
                        'content_score': float(content_score),
                        'similarity_score': float(final_score),  # 向後兼容
                        'final_score': float(final_score),
                        'match_type': match_type,
                        'weights': {
                            'title': title_weight,
                            'content': content_weight
                        },
                        'created_at': created_at,
                        'updated_at': updated_at
                    })
        
        logger.info(
            f"多向量搜索完成，返回 {len(results)} 個結果 "
            f"(weights: title={title_weight}, content={content_weight})"
        )
        return results
        
    except Exception as e:
        logger.error(f"多向量搜索失敗: {str(e)}")
        return []
```

### Step 2.2：修改 base_vector_service.py（45 分鐘）

**檔案**：`library/common/knowledge_base/base_vector_service.py`

修改 `generate_and_store_vector` 方法：

```python
def generate_and_store_vector(self, instance, action='create'):
    """
    為實例生成並存儲向量（多向量版本）
    
    Returns:
        bool: 是否成功
    """
    try:
        # 獲取 embedding 服務
        service = self._get_embedding_service()
        if not service:
            return False
        
        # 獲取標題和內容
        title = self._get_title_for_vectorization(instance)
        content = self._get_content_for_vectorization(instance)
        
        if not title and not content:
            self.logger.warning(f"實例 {instance.id} 沒有可向量化的內容")
            return False
        
        # 生成多向量
        success = service.store_document_embeddings_multi(
            source_table=self.source_table,
            source_id=instance.id,
            title=title or "",  # 如果沒有標題，使用空字串
            content=content or "",  # 如果沒有內容，使用空字串
            use_1024_table=True
        )
        
        if success:
            self.logger.info(f"✅ 多向量生成成功: {self.source_table} ID {instance.id}")
        else:
            self.logger.error(f"❌ 多向量生成失敗: {self.source_table} ID {instance.id}")
        
        return success
        
    except Exception as e:
        self.logger.error(f"多向量生成異常: {str(e)}")
        return False

def _get_title_for_vectorization(self, instance):
    """
    獲取標題用於向量化
    
    子類可以覆寫此方法來自定義標題獲取邏輯
    """
    if hasattr(instance, 'title') and instance.title:
        return instance.title
    return ""

def _get_content_for_vectorization(self, instance):
    """
    獲取內容用於向量化
    
    子類可以覆寫此方法來自定義內容獲取邏輯
    """
    # 優先使用 get_search_content 方法
    if hasattr(instance, 'get_search_content'):
        return instance.get_search_content()
    
    # 否則使用 content 屬性
    if hasattr(instance, 'content') and instance.content:
        return instance.content
    
    return ""
```

### Step 2.3：修改 vector_search_helper.py（45 分鐘）

**檔案**：`library/common/knowledge_base/vector_search_helper.py`

添加多向量搜索函數：

```python
def search_with_vectors_multi(
    query: str,
    model_class: Type[models.Model],
    source_table: str,
    limit: int = 5,
    threshold: float = 0.0,
    title_weight: float = 0.6,
    content_weight: float = 0.4,
    content_formatter: Optional[Callable] = None
) -> List[Dict[str, Any]]:
    """
    通用多向量搜尋函數
    
    Args:
        query: 查詢文本
        model_class: Django Model 類別
        source_table: 向量表中的 source_table 值
        limit: 返回結果數量
        threshold: 相似度閾值
        title_weight: 標題權重 (0.0 ~ 1.0)
        content_weight: 內容權重 (0.0 ~ 1.0)
        content_formatter: 可選的內容格式化函數
    
    Returns:
        格式化的搜尋結果列表（包含 title_score, content_score）
    """
    try:
        # 步驟 1: 多向量搜尋
        from api.services.embedding_service import get_embedding_service
        
        embedding_service = get_embedding_service('ultra_high')
        
        vector_results = embedding_service.search_similar_documents_multi(
            query=query,
            source_table=source_table,
            limit=limit,
            threshold=threshold,
            title_weight=title_weight,
            content_weight=content_weight
        )
        
        if not vector_results:
            logger.info(f"多向量搜尋無結果: {source_table}, query='{query}'")
            return []
        
        logger.info(f"多向量搜尋找到 {len(vector_results)} 條結果: {source_table}")
        
        # 步驟 2: 批量查詢 DB
        items_dict = fetch_records_by_ids(
            model_class=model_class,
            source_ids=[r['source_id'] for r in vector_results]
        )
        
        # 步驟 3: 格式化結果（包含多向量資訊）
        formatted_results = format_multi_vector_results(
            vector_results=vector_results,
            items_dict=items_dict,
            model_class=model_class,
            content_formatter=content_formatter
        )
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"通用多向量搜尋失敗 ({source_table}): {str(e)}", exc_info=True)
        return []


def format_multi_vector_results(
    vector_results: List[Dict],
    items_dict: Dict[int, models.Model],
    model_class: Type[models.Model],
    content_formatter: Optional[Callable] = None
) -> List[Dict[str, Any]]:
    """
    格式化多向量搜尋結果
    
    包含 title_score, content_score, match_type 等額外資訊
    """
    formatted_results = []
    
    for vector_result in vector_results:
        source_id = vector_result['source_id']
        
        if source_id not in items_dict:
            logger.warning(f"格式化時找不到記錄: {model_class.__name__} ID={source_id}")
            continue
        
        item = items_dict[source_id]
        
        # 獲取內容
        if content_formatter and callable(content_formatter):
            content = content_formatter(item)
        elif hasattr(item, 'get_search_content'):
            content = item.get_search_content()
        elif hasattr(item, 'content'):
            content = item.content
        else:
            content = str(item)
        
        # 組裝結果（包含多向量資訊）
        formatted_results.append({
            'content': content,
            'score': float(vector_result['final_score']),  # 主分數
            'title_score': float(vector_result['title_score']),  # ✨ 新增
            'content_score': float(vector_result['content_score']),  # ✨ 新增
            'match_type': vector_result['match_type'],  # ✨ 新增
            'weights': vector_result['weights'],  # ✨ 新增
            'title': getattr(item, 'title', str(item)),
            'metadata': {
                'id': item.id,
                'created_at': item.created_at.isoformat() if hasattr(item, 'created_at') else None,
                'updated_at': item.updated_at.isoformat() if hasattr(item, 'updated_at') else None,
            }
        })
    
    logger.info(
        f"多向量格式化完成: {model_class.__name__}, "
        f"輸入 {len(vector_results)} 條，輸出 {len(formatted_results)} 條"
    )
    
    return formatted_results
```

### Step 2.4：修改 base_search_service.py（30 分鐘）

**檔案**：`library/common/knowledge_base/base_search_service.py`

修改 `search_with_vectors` 方法以使用多向量：

```python
def search_with_vectors(self, query, limit=5, threshold=0.7, 
                       title_weight=0.6, content_weight=0.4):
    """
    使用向量進行搜索（多向量版本）
    
    Args:
        query: 查詢字串
        limit: 返回結果數量上限
        threshold: 相似度閾值 (0.0 ~ 1.0)
        title_weight: 標題權重 (0.0 ~ 1.0)
        content_weight: 內容權重 (0.0 ~ 1.0)
    """
    try:
        # 🎯 優先使用段落向量搜尋
        try:
            from .section_search_service import SectionSearchService
            section_service = SectionSearchService()
            
            section_results = section_service.search_sections(
                query=query,
                source_table=self.source_table,
                limit=limit,
                threshold=threshold
            )
            
            if section_results:
                self.logger.info(f"✅ 段落向量搜尋成功: {len(section_results)} 個結果")
                return self._format_section_results_to_standard(section_results, limit)
        except Exception as section_error:
            self.logger.warning(f"⚠️ 段落向量搜尋失敗，使用多向量搜尋: {str(section_error)}")
        
        # 備用：多向量文檔搜尋
        from .vector_search_helper import search_with_vectors_multi
        
        results = search_with_vectors_multi(
            query=query,
            model_class=self.model_class,
            source_table=self.source_table,
            limit=limit,
            threshold=threshold,
            title_weight=title_weight,
            content_weight=content_weight,
            content_formatter=self._get_item_content
        )
        
        self.logger.info(
            f"📄 多向量文檔搜尋返回 {len(results)} 個結果 "
            f"(weights: title={title_weight}, content={content_weight})"
        )
        return results
        
    except Exception as e:
        self.logger.error(f"向量搜索錯誤: {str(e)}")
        return []
```

### Step 2.5：修改 Protocol Guide 和 RVT Guide（30 分鐘）

兩個檔案都已經繼承基礎類別，不需要大改，只需確保實現正確：

**檔案**：`library/protocol_guide/vector_service.py` 和 `library/rvt_guide/vector_service.py`

確認已經有以下方法（如果沒有則添加）：

```python
def _get_title_for_vectorization(self, instance):
    """獲取標題（Protocol/RVT Guide 都有 title 欄位）"""
    return instance.title if hasattr(instance, 'title') else ""

def _get_content_for_vectorization(self, instance):
    """獲取內容（不包含標題，因為標題已分開處理）"""
    content_parts = []
    
    # 只包含 content 欄位
    if hasattr(instance, 'content') and instance.content:
        content_parts.append(instance.content)
    
    # 添加圖片摘要
    if hasattr(instance, 'get_images_summary'):
        images_summary = instance.get_images_summary()
        if images_summary:
            content_parts.append(images_summary)
    
    return ' | '.join(content_parts) if content_parts else ""
```

---

## 🔄 Phase 3：資料遷移（預計 1 小時）

### Step 3.1：創建遷移腳本（15 分鐘）

創建 Python 腳本：`scripts/regenerate_multi_vectors.py`

```python
"""
多向量資料遷移腳本

為所有現有資料重新生成標題和內容向量
"""

import os
import sys
import django

# Django 設定
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import ProtocolGuide, RVTGuide
from library.protocol_guide.vector_service import ProtocolGuideVectorService
from library.rvt_guide.vector_service import RVTGuideVectorService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def regenerate_protocol_vectors():
    """重新生成 Protocol Guide 向量"""
    logger.info("=" * 60)
    logger.info("開始重新生成 Protocol Guide 向量")
    logger.info("=" * 60)
    
    service = ProtocolGuideVectorService()
    guides = ProtocolGuide.objects.all()
    
    total = guides.count()
    success_count = 0
    failed_count = 0
    
    for i, guide in enumerate(guides, 1):
        logger.info(f"\n[{i}/{total}] 處理: {guide.title[:50]}...")
        
        try:
            if service.generate_and_store_vector(guide, action='migration'):
                success_count += 1
                logger.info(f"✅ 成功")
            else:
                failed_count += 1
                logger.error(f"❌ 失敗")
        except Exception as e:
            failed_count += 1
            logger.error(f"❌ 異常: {str(e)}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"Protocol Guide 遷移完成: 成功 {success_count}, 失敗 {failed_count}")
    logger.info("=" * 60)
    
    return success_count, failed_count


def regenerate_rvt_vectors():
    """重新生成 RVT Guide 向量"""
    logger.info("\n" + "=" * 60)
    logger.info("開始重新生成 RVT Guide 向量")
    logger.info("=" * 60)
    
    service = RVTGuideVectorService()
    guides = RVTGuide.objects.all()
    
    total = guides.count()
    success_count = 0
    failed_count = 0
    
    for i, guide in enumerate(guides, 1):
        logger.info(f"\n[{i}/{total}] 處理: {guide.title[:50]}...")
        
        try:
            if service.generate_and_store_vector(guide, action='migration'):
                success_count += 1
                logger.info(f"✅ 成功")
            else:
                failed_count += 1
                logger.error(f"❌ 失敗")
        except Exception as e:
            failed_count += 1
            logger.error(f"❌ 異常: {str(e)}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"RVT Guide 遷移完成: 成功 {success_count}, 失敗 {failed_count}")
    logger.info("=" * 60)
    
    return success_count, failed_count


def verify_migration():
    """驗證遷移結果"""
    from django.db import connection
    
    logger.info("\n" + "=" * 60)
    logger.info("驗證遷移結果")
    logger.info("=" * 60)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                source_table,
                COUNT(*) as total,
                COUNT(title_embedding) as has_title,
                COUNT(content_embedding) as has_content,
                COUNT(CASE WHEN title_embedding IS NOT NULL AND content_embedding IS NOT NULL THEN 1 END) as complete
            FROM document_embeddings
            GROUP BY source_table
            ORDER BY source_table;
        """)
        
        results = cursor.fetchall()
        
        logger.info("\n向量統計：")
        logger.info(f"{'來源表':<20} {'總數':<10} {'有標題':<10} {'有內容':<10} {'完整':<10}")
        logger.info("-" * 60)
        
        for row in results:
            source_table, total, has_title, has_content, complete = row
            logger.info(f"{source_table:<20} {total:<10} {has_title:<10} {has_content:<10} {complete:<10}")
        
        # 檢查完整性
        cursor.execute("""
            SELECT COUNT(*) 
            FROM document_embeddings 
            WHERE title_embedding IS NULL OR content_embedding IS NULL;
        """)
        incomplete_count = cursor.fetchone()[0]
        
        if incomplete_count > 0:
            logger.warning(f"\n⚠️ 警告：有 {incomplete_count} 筆記錄的向量不完整")
            return False
        else:
            logger.info(f"\n✅ 所有向量都已完整生成")
            return True


if __name__ == '__main__':
    try:
        # 重新生成 Protocol Guide 向量
        protocol_success, protocol_failed = regenerate_protocol_vectors()
        
        # 重新生成 RVT Guide 向量
        rvt_success, rvt_failed = regenerate_rvt_vectors()
        
        # 驗證結果
        is_complete = verify_migration()
        
        # 總結
        logger.info("\n" + "=" * 60)
        logger.info("遷移總結")
        logger.info("=" * 60)
        logger.info(f"Protocol Guide: 成功 {protocol_success}, 失敗 {protocol_failed}")
        logger.info(f"RVT Guide: 成功 {rvt_success}, 失敗 {rvt_failed}")
        logger.info(f"總計: 成功 {protocol_success + rvt_success}, 失敗 {protocol_failed + rvt_failed}")
        logger.info(f"遷移狀態: {'✅ 完成' if is_complete and protocol_failed == 0 and rvt_failed == 0 else '❌ 有錯誤'}")
        logger.info("=" * 60)
        
        sys.exit(0 if is_complete and protocol_failed == 0 and rvt_failed == 0 else 1)
        
    except Exception as e:
        logger.error(f"\n❌ 遷移失敗: {str(e)}", exc_info=True)
        sys.exit(1)
```

### Step 3.2：執行遷移（30 分鐘）

```bash
# 複製腳本到容器
docker cp scripts/regenerate_multi_vectors.py ai-django:/app/scripts/

# 執行遷移
docker exec ai-django python scripts/regenerate_multi_vectors.py

# 預期輸出：
# ==========================================================
# 開始重新生成 Protocol Guide 向量
# ==========================================================
# [1/5] 處理: ULINK Protocol 連接測試指南...
# ✅ 成功
# [2/5] 處理: ...
# ...
# Protocol Guide 遷移完成: 成功 5, 失敗 0
# 
# ==========================================================
# 開始重新生成 RVT Guide 向量
# ==========================================================
# [1/2] 處理: RVT 測試指南...
# ✅ 成功
# ...
# RVT Guide 遷移完成: 成功 2, 失敗 0
#
# ✅ 所有向量都已完整生成
```

### Step 3.3：驗證遷移結果（15 分鐘）

```bash
# 檢查向量完整性
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT 
    source_table,
    COUNT(*) as total,
    COUNT(embedding) as old_vectors,
    COUNT(title_embedding) as title_vectors,
    COUNT(content_embedding) as content_vectors,
    COUNT(CASE WHEN title_embedding IS NOT NULL AND content_embedding IS NOT NULL THEN 1 END) as complete_records
FROM document_embeddings
GROUP BY source_table
ORDER BY source_table;
"

# 預期結果：
#   source_table  | total | old_vectors | title_vectors | content_vectors | complete_records 
# ----------------+-------+-------------+---------------+-----------------+------------------
#  protocol_guide |     5 |           5 |             5 |               5 |                5
#  rvt_guide      |     2 |           2 |             2 |               2 |                2

# 檢查向量維度
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT 
    vector_dims(title_embedding) as title_dims,
    vector_dims(content_embedding) as content_dims
FROM document_embeddings
LIMIT 1;
"

# 預期結果：
#  title_dims | content_dims 
# ------------+--------------
#        1024 |         1024
```

---

## 🧪 Phase 4：測試驗證（預計 4 小時）

### Step 4.1：單元測試（90 分鐘）

創建測試腳本：`tests/test_multi_vector.py`

```python
"""
多向量功能測試
"""

import pytest
from api.models import ProtocolGuide
from library.protocol_guide.vector_service import ProtocolGuideVectorService
from library.protocol_guide.search_service import ProtocolGuideSearchService
from api.services.embedding_service import get_embedding_service


class TestMultiVectorGeneration:
    """測試多向量生成"""
    
    def test_generate_multi_vectors(self):
        """測試生成標題和內容向量"""
        service = ProtocolGuideVectorService()
        guide = ProtocolGuide.objects.first()
        
        # 生成向量
        success = service.generate_and_store_vector(guide)
        
        assert success is True
        
        # 驗證向量已儲存
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    title_embedding IS NOT NULL as has_title,
                    content_embedding IS NOT NULL as has_content
                FROM document_embeddings
                WHERE source_table = 'protocol_guide' AND source_id = %s;
            """, [guide.id])
            
            result = cursor.fetchone()
            assert result[0] is True  # has_title
            assert result[1] is True  # has_content


class TestMultiVectorSearch:
    """測試多向量搜索"""
    
    def test_search_with_title_focus(self):
        """測試強調標題的搜索"""
        service = ProtocolGuideSearchService()
        
        # 搜索（強調標題）
        results = service.search_with_vectors(
            query="ULINK 測試",
            limit=5,
            threshold=0.5,
            title_weight=0.8,
            content_weight=0.2
        )
        
        assert len(results) > 0
        
        # 驗證結果包含分數資訊
        first_result = results[0]
        assert 'title_score' in first_result
        assert 'content_score' in first_result
        assert 'match_type' in first_result
        assert 'weights' in first_result
    
    def test_search_with_content_focus(self):
        """測試強調內容的搜索"""
        service = ProtocolGuideSearchService()
        
        # 搜索（強調內容）
        results = service.search_with_vectors(
            query="如何設定參數",
            limit=5,
            threshold=0.5,
            title_weight=0.3,
            content_weight=0.7
        )
        
        assert len(results) > 0
        
        # 驗證權重配置
        first_result = results[0]
        assert first_result['weights']['title'] == 0.3
        assert first_result['weights']['content'] == 0.7
    
    def test_compare_single_vs_multi_vector(self):
        """對比單向量和多向量搜索結果"""
        embedding_service = get_embedding_service('ultra_high')
        
        query = "ULINK 連接測試"
        
        # 單向量搜索（舊方法）
        single_results = embedding_service.search_similar_documents(
            query=query,
            source_table='protocol_guide',
            limit=5,
            threshold=0.5
        )
        
        # 多向量搜索（新方法）
        multi_results = embedding_service.search_similar_documents_multi(
            query=query,
            source_table='protocol_guide',
            limit=5,
            threshold=0.5,
            title_weight=0.6,
            content_weight=0.4
        )
        
        # 驗證多向量有額外資訊
        assert len(multi_results) > 0
        assert 'title_score' in multi_results[0]
        assert 'content_score' in multi_results[0]
        assert 'match_type' in multi_results[0]


class TestWeightAdjustment:
    """測試權重調整"""
    
    @pytest.mark.parametrize("title_weight,content_weight", [
        (0.8, 0.2),
        (0.6, 0.4),
        (0.4, 0.6),
        (0.2, 0.8),
    ])
    def test_different_weights(self, title_weight, content_weight):
        """測試不同權重配置"""
        service = ProtocolGuideSearchService()
        
        results = service.search_with_vectors(
            query="測試",
            limit=3,
            threshold=0.3,
            title_weight=title_weight,
            content_weight=content_weight
        )
        
        assert len(results) >= 0
        
        if len(results) > 0:
            # 驗證權重正確應用
            assert results[0]['weights']['title'] == title_weight
            assert results[0]['weights']['content'] == content_weight
```

執行測試：

```bash
# 進入容器
docker exec -it ai-django bash

# 執行測試
python -m pytest tests/test_multi_vector.py -v

# 預期輸出：
# tests/test_multi_vector.py::TestMultiVectorGeneration::test_generate_multi_vectors PASSED
# tests/test_multi_vector.py::TestMultiVectorSearch::test_search_with_title_focus PASSED
# tests/test_multi_vector.py::TestMultiVectorSearch::test_search_with_content_focus PASSED
# tests/test_multi_vector.py::TestMultiVectorSearch::test_compare_single_vs_multi_vector PASSED
# tests/test_multi_vector.py::TestWeightAdjustment::test_different_weights[0.8-0.2] PASSED
# tests/test_multi_vector.py::TestWeightAdjustment::test_different_weights[0.6-0.4] PASSED
# tests/test_multi_vector.py::TestWeightAdjustment::test_different_weights[0.4-0.6] PASSED
# tests/test_multi_vector.py::TestWeightAdjustment::test_different_weights[0.2-0.8] PASSED
```

### Step 4.2：整合測試（90 分鐘）

測試完整的搜索流程，包括向量搜索和關鍵字搜索的混合。

### Step 4.3：效能測試（60 分鐘）

測試多向量搜索的效能，對比單向量方法。

---

## ✅ 實施後檢查清單

### 功能驗證

- [ ] **向量生成**：Protocol 和 RVT Guide 都能正確生成多向量
- [ ] **向量搜索**：搜索功能正常，返回正確結果
- [ ] **權重調整**：不同權重配置產生不同排序
- [ ] **分數資訊**：返回結果包含 title_score, content_score, match_type
- [ ] **向後兼容**：舊的單向量搜索仍然可用（如果需要）

### 效能驗證

- [ ] **生成時間**：單筆向量生成 < 0.5 秒
- [ ] **搜索時間**：單次搜索 < 0.15 秒
- [ ] **記憶體使用**：容器記憶體使用正常
- [ ] **磁碟空間**：資料庫大小增加合理（約 2 倍）

### 資料驗證

- [ ] **向量完整性**：所有記錄都有 title_embedding 和 content_embedding
- [ ] **向量維度**：所有向量都是 1024 維
- [ ] **索引狀態**：兩個新索引都已創建

---

## 🔄 回滾計劃（如果出現問題）

### 快速回滾（< 5 分鐘）

如果在測試階段發現嚴重問題：

```bash
# 1. 停止應用
docker compose stop ai-django ai-react

# 2. 恢復資料庫
docker exec -i postgres_db psql -U postgres -d ai_platform < \
  /home/user/codes/ai-platform-web/backups/multi-vector-migration/backup_YYYYMMDD_HHMMSS.sql

# 3. 還原程式碼（如果有提交）
git checkout HEAD~1

# 4. 重啟應用
docker compose start ai-django ai-react
```

### 部分回滾（保留資料）

如果只是程式碼有問題，資料庫遷移正常：

```bash
# 還原程式碼到上一個版本
git checkout HEAD~1

# 重啟容器
docker compose restart ai-django
```

---

## 📊 成功標準

### 功能標準

✅ 所有單元測試通過  
✅ 所有整合測試通過  
✅ Protocol Assistant 搜索功能正常  
✅ RVT Assistant 搜索功能正常  
✅ 權重調整功能正常  
✅ 回傳結果包含多向量資訊

### 效能標準

✅ 向量生成時間 < 0.5 秒/筆  
✅ 搜索回應時間 < 0.15 秒  
✅ 容器 CPU 使用率 < 80%  
✅ 容器記憶體使用 < 2GB  
✅ 資料庫連接池健康

### 品質標準

✅ 程式碼通過 lint 檢查  
✅ 所有函數有文檔字串  
✅ 關鍵邏輯有日誌記錄  
✅ 錯誤處理完善  
✅ 測試覆蓋率 > 80%

---

## 📝 實施檢查表（執行時使用）

```
□ Phase 1: 資料庫結構修改
  □ Step 1.1: 備份資料庫
  □ Step 1.2: 創建 SQL 腳本
  □ Step 1.3: 執行遷移
  □ 驗證：表結構正確

□ Phase 2: 程式碼修改
  □ Step 2.1: embedding_service.py
  □ Step 2.2: base_vector_service.py
  □ Step 2.3: vector_search_helper.py
  □ Step 2.4: base_search_service.py
  □ Step 2.5: Protocol/RVT vector_service.py
  □ 驗證：程式碼無語法錯誤

□ Phase 3: 資料遷移
  □ Step 3.1: 創建遷移腳本
  □ Step 3.2: 執行遷移
  □ Step 3.3: 驗證結果
  □ 驗證：所有向量完整

□ Phase 4: 測試驗證
  □ Step 4.1: 單元測試
  □ Step 4.2: 整合測試
  □ Step 4.3: 效能測試
  □ 驗證：所有測試通過

□ 最終檢查
  □ 功能驗證完成
  □ 效能符合標準
  □ 文檔已更新
  □ 備份已確認
```

---

**準備好了嗎？讓我們開始實施！** 🚀
