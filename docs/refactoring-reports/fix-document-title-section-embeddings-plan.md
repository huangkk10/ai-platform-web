# 修復文檔標題段落向量缺失問題 - 完整計劃

## 🎯 問題總結

### 根本原因
- **現象**：Stage 1 搜尋「CrystalDiskMark 是什麼」時，無法找到 CrystalDiskMark 5 文檔
- **原因**：文檔標題段落（`is_document_title=true`）沒有生成 `title_embedding` 和 `content_embedding`
- **影響**：即使 Stage 1 設定 95% 標題權重，仍無法匹配最佳結果（因為最佳標題被 SQL 過濾器排除）

### 受影響範圍
```sql
-- 統計結果
| 知識庫 | 總段落數 | 文檔標題段落 | 缺失向量的文檔標題段落 |
|--------|---------|-------------|----------------------|
| rvt_guide | 53 | 0 | 0 ✅ |
| protocol_guide | 341 | 4 | 4 ❌ |
```

### 受影響的文檔
| 段落 ID | 文檔 ID | 標題 | 文檔長度 | word_count |
|---------|---------|------|---------|-----------|
| 162 | 10 | **UNH-IOL** | 1,219 字元 | 0 |
| 159 | 15 | **Burn in Test** | 1,139 字元 | 0 |
| 160 | 16 | **CrystalDiskMark 5** ⭐ | 784 字元 | 0 |
| 163 | 17 | **阿呆** | 147 字元 | 0 |

---

## 📋 完整修復方案（兩個層面）

### 🔧 層面 1：立即修復（補救現有資料）

**目標**：為已經存在的 4 個文檔標題段落生成向量

**腳本**：`backend/fix_document_title_embeddings.py`

```python
#!/usr/bin/env python
"""
修復文檔標題段落的向量缺失問題

此腳本會：
1. 查詢所有 is_document_title=true 且向量為 NULL 的段落
2. 為每個段落生成 title_embedding 和 content_embedding
3. 更新 document_section_embeddings 表
"""

import os
import sys
import django

# Django 設定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.services.embedding_service import get_embedding_service
from django.db import connection
import logging

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fix_document_title_embeddings(source_table='protocol_guide'):
    """
    為文檔標題段落生成向量
    
    Args:
        source_table: 來源表名稱 (protocol_guide 或 rvt_guide)
    """
    logger.info(f"🚀 開始修復 {source_table} 的文檔標題段落向量")
    
    service = get_embedding_service()
    
    # 查詢沒有向量的文檔標題段落
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT 
                dse.id, 
                dse.source_id,
                dse.heading_text,
                COALESCE(pg.content, ''),
                COALESCE(pg.title, dse.heading_text)
            FROM document_section_embeddings dse
            LEFT JOIN {source_table} pg ON pg.id = dse.source_id
            WHERE dse.source_table = %s
              AND dse.is_document_title = true
              AND dse.title_embedding IS NULL
            ORDER BY dse.source_id
        """, [source_table])
        
        sections = cursor.fetchall()
    
    if not sections:
        logger.info(f"✅ {source_table} 沒有需要修復的文檔標題段落")
        return
    
    logger.info(f"📊 發現 {len(sections)} 個需要修復的文檔標題段落")
    
    success_count = 0
    fail_count = 0
    
    for section_id, doc_id, heading_text, content, doc_title in sections:
        try:
            logger.info(f"\n處理段落 ID={section_id}, 文檔 ID={doc_id}")
            logger.info(f"  標題: {heading_text}")
            logger.info(f"  文檔長度: {len(content)} 字元")
            
            # 生成標題向量（使用段落標題）
            title_text = heading_text or doc_title
            logger.info(f"  生成標題向量: '{title_text}'")
            title_embedding = service.generate_embedding(title_text)
            
            # 生成內容向量（使用文檔前 500 字元或完整內容）
            if content and len(content) > 0:
                # 取前 500 字元（約 1000 tokens）
                content_preview = content[:500]
                logger.info(f"  生成內容向量: 使用前 {len(content_preview)} 字元")
            else:
                # 如果沒有內容，使用標題
                content_preview = title_text
                logger.info(f"  生成內容向量: 使用標題（無內容）")
            
            content_embedding = service.generate_embedding(content_preview)
            
            # 計算 word_count（如果需要）
            word_count = len(content_preview.split()) if content_preview else 0
            
            # 更新資料庫
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE document_section_embeddings
                    SET title_embedding = %s,
                        content_embedding = %s,
                        word_count = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, [title_embedding, content_embedding, word_count, section_id])
            
            logger.info(f"  ✅ 成功: 段落 ID={section_id}, '{heading_text}'")
            success_count += 1
            
        except Exception as e:
            logger.error(f"  ❌ 失敗: 段落 ID={section_id}, 錯誤: {str(e)}")
            fail_count += 1
    
    logger.info(f"\n{'='*60}")
    logger.info(f"修復完成: {success_count} 成功, {fail_count} 失敗")
    logger.info(f"{'='*60}")


def verify_fix(source_table='protocol_guide'):
    """驗證修復結果"""
    logger.info(f"\n🔍 驗證 {source_table} 的修復結果")
    
    with connection.cursor() as cursor:
        # 檢查是否還有未修復的
        cursor.execute("""
            SELECT COUNT(*)
            FROM document_section_embeddings
            WHERE source_table = %s
              AND is_document_title = true
              AND title_embedding IS NULL
        """, [source_table])
        
        remaining = cursor.fetchone()[0]
        
        if remaining == 0:
            logger.info(f"✅ 所有文檔標題段落都已有向量")
        else:
            logger.warning(f"⚠️  還有 {remaining} 個文檔標題段落缺少向量")
        
        # 列出所有文檔標題段落的狀態
        cursor.execute("""
            SELECT 
                dse.id,
                dse.heading_text,
                dse.title_embedding IS NOT NULL as has_title_vec,
                dse.content_embedding IS NOT NULL as has_content_vec,
                vector_dims(dse.title_embedding) as title_dims,
                vector_dims(dse.content_embedding) as content_dims
            FROM document_section_embeddings dse
            WHERE dse.source_table = %s
              AND dse.is_document_title = true
            ORDER BY dse.id
        """, [source_table])
        
        results = cursor.fetchall()
        
        logger.info(f"\n文檔標題段落狀態:")
        logger.info(f"{'ID':<6} {'標題':<25} {'Title Vec':<10} {'Content Vec':<12} {'Dims':<8}")
        logger.info(f"{'-'*70}")
        
        for row in results:
            section_id, title, has_title, has_content, title_dims, content_dims = row
            title_display = title[:22] + '...' if len(title) > 25 else title
            dims = f"{title_dims}/{content_dims}" if title_dims and content_dims else "N/A"
            status = "✅" if has_title and has_content else "❌"
            logger.info(f"{section_id:<6} {title_display:<25} {str(has_title):<10} {str(has_content):<12} {dims:<8} {status}")


if __name__ == '__main__':
    print("=" * 60)
    print("修復文檔標題段落向量缺失問題")
    print("=" * 60)
    
    # 修復 protocol_guide
    fix_document_title_embeddings('protocol_guide')
    verify_fix('protocol_guide')
    
    # 修復 rvt_guide（如果需要）
    print("\n" + "=" * 60)
    fix_document_title_embeddings('rvt_guide')
    verify_fix('rvt_guide')
    
    print("\n" + "=" * 60)
    print("✅ 修復完成！")
    print("=" * 60)
```

**執行方式**：
```bash
# 進入 Django 容器
docker exec -it ai-django bash

# 執行修復腳本
cd /app
python fix_document_title_embeddings.py
```

---

### 🛠️ 層面 2：根治問題（修改向量生成邏輯）

**目標**：確保未來新增/修改文章時，文檔標題段落會自動生成向量

#### 步驟 2.1：定位向量生成代碼

需要檢查的檔案位置：

1. **Protocol Assistant 向量生成**
   ```
   library/protocol_guide/vector_service.py
   ```

2. **RVT Assistant 向量生成**
   ```
   library/rvt_guide/vector_service.py
   ```

3. **通用段落向量服務**
   ```
   library/common/knowledge_base/base_vector_service.py
   library/common/knowledge_base/section_vector_service.py
   ```

4. **ViewSet Manager（觸發向量生成的地方）**
   ```
   library/protocol_guide/viewset_manager.py
   library/rvt_guide/viewset_manager.py
   ```

#### 步驟 2.2：檢查當前邏輯

查找可能跳過文檔標題段落的邏輯：

```python
# 🔍 可能的問題代碼模式

# 模式 1: 跳過空內容段落
if not section.content or len(section.content.strip()) == 0:
    continue  # ⚠️ 這會跳過 word_count=0 的段落

# 模式 2: 跳過文檔標題段落
if section.is_document_title:
    continue  # ⚠️ 明確跳過

# 模式 3: 只處理有內容的段落
if section.word_count > 0:
    # 只處理有單詞的段落
    pass
else:
    continue  # ⚠️ 跳過 word_count=0
```

#### 步驟 2.3：修改向量生成邏輯

**修改位置**：`library/common/knowledge_base/section_vector_service.py`

```python
# 修改前（假設的問題代碼）
def generate_section_embeddings(self, section):
    """生成段落向量"""
    
    # ❌ 問題：跳過空內容段落
    if not section.content or section.word_count == 0:
        logger.debug(f"跳過空內容段落: {section.id}")
        return None
    
    # ... 生成向量
```

```python
# 修改後（正確邏輯）
def generate_section_embeddings(self, section):
    """生成段落向量"""
    
    # ✅ 特殊處理：文檔標題段落
    if section.is_document_title:
        logger.info(f"生成文檔標題段落向量: {section.id}, '{section.heading_text}'")
        
        # 標題向量：使用段落標題
        title_embedding = self.embedding_service.generate_embedding(
            section.heading_text
        )
        
        # 內容向量：使用文檔前 500 字元
        document = self._get_source_document(section.source_table, section.source_id)
        if document and document.content:
            content_preview = document.content[:500]
        else:
            # 如果沒有內容，使用標題
            content_preview = section.heading_text
        
        content_embedding = self.embedding_service.generate_embedding(
            content_preview
        )
        
        return {
            'title_embedding': title_embedding,
            'content_embedding': content_embedding,
            'word_count': len(content_preview.split())
        }
    
    # ✅ 一般段落：跳過空內容
    if not section.content or section.word_count == 0:
        logger.debug(f"跳過空內容段落（非文檔標題）: {section.id}")
        return None
    
    # ... 原有的生成向量邏輯
```

#### 步驟 2.4：修改 ViewSet Manager

確保 `perform_create` 和 `perform_update` 會觸發文檔標題段落向量生成：

```python
# library/protocol_guide/viewset_manager.py
# library/rvt_guide/viewset_manager.py

class ProtocolGuideViewSetManager(BaseKnowledgeBaseViewSetManager):
    """Protocol Guide ViewSet 管理器"""
    
    def perform_create(self, serializer):
        """創建文檔時生成向量"""
        instance = serializer.save()
        
        logger.info(f"📝 新增文檔: ID={instance.id}, 標題='{instance.title}'")
        
        # ✅ 生成段落向量（包括文檔標題段落）
        self.generate_section_embeddings_for_document(instance)
        
        return instance
    
    def perform_update(self, serializer):
        """更新文檔時重新生成向量"""
        instance = serializer.save()
        
        logger.info(f"✏️  更新文檔: ID={instance.id}, 標題='{instance.title}'")
        
        # ✅ 重新生成段落向量（包括文檔標題段落）
        self.regenerate_section_embeddings_for_document(instance)
        
        return instance
    
    def generate_section_embeddings_for_document(self, document):
        """為文檔生成所有段落的向量"""
        try:
            # 調用段落向量服務
            section_service = self.get_section_vector_service()
            section_service.generate_embeddings_for_document(
                source_table=self.source_table,
                source_id=document.id,
                force_regenerate=False  # 只生成缺失的
            )
            
            logger.info(f"✅ 文檔段落向量生成完成: ID={document.id}")
            
        except Exception as e:
            logger.error(f"❌ 文檔段落向量生成失敗: ID={document.id}, 錯誤: {str(e)}")
            # 不阻止文檔創建/更新
    
    def regenerate_section_embeddings_for_document(self, document):
        """重新生成文檔的所有段落向量"""
        try:
            section_service = self.get_section_vector_service()
            section_service.generate_embeddings_for_document(
                source_table=self.source_table,
                source_id=document.id,
                force_regenerate=True  # 強制重新生成所有段落
            )
            
            logger.info(f"✅ 文檔段落向量重新生成完成: ID={document.id}")
            
        except Exception as e:
            logger.error(f"❌ 文檔段落向量重新生成失敗: ID={document.id}, 錯誤: {str(e)}")
```

#### 步驟 2.5：添加資料驗證

在向量生成後檢查文檔標題段落是否有向量：

```python
def validate_document_section_embeddings(source_table, source_id):
    """
    驗證文檔的段落向量完整性
    
    檢查項目：
    1. 是否有 is_document_title=true 的段落
    2. 文檔標題段落是否有向量
    3. 所有段落的向量維度是否正確
    """
    with connection.cursor() as cursor:
        # 檢查文檔標題段落
        cursor.execute("""
            SELECT 
                id,
                heading_text,
                is_document_title,
                title_embedding IS NULL as no_title_vec,
                content_embedding IS NULL as no_content_vec
            FROM document_section_embeddings
            WHERE source_table = %s
              AND source_id = %s
              AND is_document_title = true
        """, [source_table, source_id])
        
        doc_title_sections = cursor.fetchall()
        
        if not doc_title_sections:
            logger.warning(
                f"⚠️  文檔 {source_table}.{source_id} 沒有文檔標題段落 "
                f"(is_document_title=true)"
            )
            return False
        
        # 檢查向量完整性
        for section_id, heading, is_doc_title, no_title, no_content in doc_title_sections:
            if no_title or no_content:
                logger.error(
                    f"❌ 文檔標題段落缺少向量: "
                    f"段落 ID={section_id}, 標題='{heading}', "
                    f"缺少 title_vec={no_title}, 缺少 content_vec={no_content}"
                )
                return False
        
        logger.info(f"✅ 文檔 {source_table}.{source_id} 的段落向量完整")
        return True
```

---

## 🧪 測試計劃

### 測試 1：立即修復（補救現有資料）

```bash
# 1. 執行修復腳本
docker exec -it ai-django python fix_document_title_embeddings.py

# 2. 驗證修復結果
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT 
    id,
    heading_text,
    title_embedding IS NOT NULL as has_title,
    content_embedding IS NOT NULL as has_content,
    vector_dims(title_embedding) as title_dims,
    vector_dims(content_embedding) as content_dims
FROM document_section_embeddings
WHERE source_table = 'protocol_guide'
  AND is_document_title = true
ORDER BY id;
"

# 預期結果：4 個段落都應該有 1024 維向量
```

### 測試 2：新增文章（驗證自動生成）

**Protocol Assistant 測試**：
```bash
# 1. 透過 Web UI 新增一篇測試文章
標題: "測試向量自動生成"
內容: "這是一篇測試文章，用於驗證文檔標題段落是否會自動生成向量。"

# 2. 檢查資料庫
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT 
    dse.id,
    dse.source_id,
    dse.heading_text,
    dse.is_document_title,
    dse.title_embedding IS NOT NULL as has_title_vec,
    dse.content_embedding IS NOT NULL as has_content_vec,
    vector_dims(dse.title_embedding) as dims
FROM document_section_embeddings dse
WHERE dse.source_table = 'protocol_guide'
  AND dse.source_id = (
    SELECT id FROM protocol_guide 
    WHERE title = '測試向量自動生成'
  )
  AND dse.is_document_title = true;
"

# 預期結果：
# - 找到 1 個段落
# - is_document_title = true
# - has_title_vec = true
# - has_content_vec = true
# - dims = 1024
```

**RVT Assistant 測試**：
```bash
# 同樣流程，測試 rvt_guide
```

### 測試 3：修改文章（驗證向量更新）

```bash
# 1. 修改文章標題
原標題: "測試向量自動生成"
新標題: "測試向量自動生成【已修改】"

# 2. 檢查向量是否更新
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT 
    dse.heading_text,
    dse.updated_at,
    pg.updated_at as doc_updated_at
FROM document_section_embeddings dse
LEFT JOIN protocol_guide pg ON pg.id = dse.source_id
WHERE dse.source_table = 'protocol_guide'
  AND dse.is_document_title = true
  AND pg.title LIKE '測試向量自動生成%'
ORDER BY dse.updated_at DESC;
"

# 預期結果：
# - heading_text = "測試向量自動生成【已修改】"
# - dse.updated_at 應該 >= doc_updated_at（向量已更新）
```

### 測試 4：搜尋準確度（驗證修復效果）

```bash
# 重新執行 Stage 1 測試
cd /app
python tests/test_stage1_sql_direct.py

# 預期結果：
# CrystalDiskMark 5 (ID=160) 應該出現在 top 10 中，且排名靠前
```

---

## 📊 預期效果

### 修復前
```
查詢: "CrystalDiskMark 是什麼"

Stage 1 (95% 標題權重) Top 10:
1. Kingston KC3000 - 0.82
2. ULINK_A - 0.81
3. PCIeCV - 0.79
...
10. Burn in Test - 0.72

❌ CrystalDiskMark 5 不在列表中（ID=160 被過濾）
```

### 修復後
```
查詢: "CrystalDiskMark 是什麼"

Stage 1 (95% 標題權重) Top 10:
1. CrystalDiskMark 5 (ID=160) - 0.96 ⭐ 完美匹配！
2. Kingston KC3000 - 0.82
3. ULINK_A - 0.81
...

✅ CrystalDiskMark 5 在第 1 名
✅ Stage 1 直接返回正確結果，不需要 Stage 2
```

---

## 🎯 執行順序

### 階段 1：立即修復（今天可執行）
1. ✅ 創建 `fix_document_title_embeddings.py` 腳本
2. ✅ 執行腳本，修復 4 個文檔標題段落
3. ✅ 驗證修復結果
4. ✅ 測試 Stage 1 搜尋準確度

### 階段 2：根治問題（需要代碼審查）
1. 🔍 定位向量生成邏輯的位置
2. 🔍 檢查是否跳過了文檔標題段落
3. ✏️  修改向量生成邏輯（包含文檔標題段落）
4. ✏️  修改 ViewSet Manager（確保觸發向量生成）
5. ✏️  添加資料驗證（檢查完整性）

### 階段 3：全面測試
1. 🧪 測試新增文章（Protocol + RVT）
2. 🧪 測試修改文章（驗證向量更新）
3. 🧪 測試搜尋準確度（確認修復效果）
4. 📝 記錄測試結果

---

## 🔧 相關檔案清單

### 需要創建
- ✅ `backend/fix_document_title_embeddings.py` - 立即修復腳本

### 需要檢查
- `library/protocol_guide/vector_service.py`
- `library/rvt_guide/vector_service.py`
- `library/common/knowledge_base/base_vector_service.py`
- `library/common/knowledge_base/section_vector_service.py`
- `library/protocol_guide/viewset_manager.py`
- `library/rvt_guide/viewset_manager.py`

### 需要修改（可能）
- `library/common/knowledge_base/section_vector_service.py` - 添加文檔標題段落處理邏輯
- `library/protocol_guide/viewset_manager.py` - 確保觸發向量生成
- `library/rvt_guide/viewset_manager.py` - 確保觸發向量生成

### 測試腳本
- `tests/test_stage1_sql_direct.py` - 驗證修復效果
- `tests/test_document_title_embedding_generation.py` - 新增/修改文章測試（需創建）

---

## 📚 參考文檔

- **向量搜尋指南**: `/docs/vector-search/vector-search-guide.md`
- **Stage 1/2 搜尋分析**: `/docs/troubleshooting/stage1-stage2-search-analysis.md`
- **文檔標題段落問題**: 本文檔

---

**更新日期**：2025-11-26  
**文檔類型**：重構計劃  
**優先級**：HIGH  
**預估時間**：階段 1（2 小時），階段 2（1 天）
