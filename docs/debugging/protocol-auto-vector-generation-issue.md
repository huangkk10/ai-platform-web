# Protocol Guide 自動向量生成問題與解決方案

**發現日期**：2025-11-11  
**問題類型**：系統設計缺陷  
**優先級**：中高

---

## 📋 問題總結

**您的問題**：「當建立了新的 Protocol Guide 或是修改，會可能沒有產生對應的欄位或資料，是嗎?」

**答案**：**是的，但有條件限制**

| 創建方式 | 是否自動生成向量 | 原因 |
|---------|----------------|------|
| **REST API 創建/修改** | ✅ 會自動生成 | ViewSet 的 `perform_create/update` 被觸發 |
| **Django ORM 創建/修改** | ❌ 不會自動生成 | ViewSet 方法不被觸發，沒有 Django signals |
| **Django Admin 後台** | ❌ 不會自動生成 | 同上，使用 ORM 方式 |
| **測試腳本 (ORM)** | ❌ 不會自動生成 | 同上 |
| **Management Command** | ❌ 不會自動生成 | 同上 |

---

## 🔍 詳細分析

### 現有的自動向量生成機制

#### ✅ 透過 API 創建（正常工作）

```python
# 前端或 curl 呼叫
POST /api/protocol-guides/
{
    "title": "測試文檔",
    "content": "# 內容..."
}

# 後端處理流程：
# 1. Request → ProtocolGuideViewSet
# 2. ViewSet.create() → perform_create(serializer)
# 3. perform_create() 內部：
#    a. serializer.save() → 創建 Protocol Guide
#    b. 生成整篇文檔向量（舊系統）
#    c. 生成段落向量（新系統，包含 document_id）
```

**結果**：✅ 所有向量欄位都正確生成

#### ❌ 透過 ORM 創建（不會觸發）

```python
# 在 Django shell、測試、或 Admin 中
guide = ProtocolGuide.objects.create(
    title="測試文檔",
    content="# 內容..."
)

# 處理流程：
# 1. Django ORM 直接寫入資料庫
# 2. ProtocolGuide 表有新記錄
# 3. ❌ ViewSet.perform_create() 不被觸發
# 4. ❌ 沒有 Django signals (post_save)
# 5. 結果：document_section_embeddings 表沒有記錄
```

**結果**：❌ 沒有任何向量生成

---

## 🧪 實際驗證

### 測試結果

```bash
$ docker exec ai-django python test_new_protocol_guide_creation.py

✅ 文檔創建成功，ID: 22
❌ 沒有找到段落向量！文檔 22 的向量生成失敗
```

**確認問題存在**：
- Protocol Guide ID 22 成功創建在 `protocol_guide` 表
- 但 `document_section_embeddings` 表沒有對應的記錄
- 原因：測試腳本使用 `ProtocolGuide.objects.create()`（ORM 方式）

---

## ✅ 解決方案

### 方案 1：添加 Django Signals（推薦）⭐

**優點**：
- ✅ 所有創建方式都會自動生成向量
- ✅ 統一處理邏輯
- ✅ 符合 Django 最佳實踐
- ✅ 不需要修改現有代碼

**缺點**：
- ⚠️ 增加系統複雜度
- ⚠️ 可能影響批量操作性能

#### 實作步驟

**步驟 1：創建 signals.py**

```python
# backend/api/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from api.models import ProtocolGuide, RVTGuide
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ProtocolGuide)
def protocol_guide_post_save(sender, instance, created, **kwargs):
    """
    Protocol Guide 儲存後自動生成/更新向量
    
    Args:
        sender: ProtocolGuide Model
        instance: 儲存的實例
        created: 是否為新創建（True）或更新（False）
    """
    from library.common.knowledge_base.section_vectorization_service import SectionVectorizationService
    from api.services.embedding_service import get_embedding_service
    
    action = 'create' if created else 'update'
    logger.info(f"🔔 Signal 觸發: Protocol Guide {instance.id} {action}")
    
    try:
        # 1. 生成/更新整篇文檔向量（舊系統，1024 維）
        embedding_service = get_embedding_service('ultra_high')
        content = f"Title: {instance.title}\n\nContent:\n{instance.content}"
        
        embedding_service.store_document_embedding(
            source_table='protocol_guide',
            source_id=instance.id,
            content=content,
            use_1024_table=True
        )
        logger.info(f"  ✅ 整篇文檔向量{'生成' if created else '更新'}成功")
        
        # 2. 生成/更新段落向量（新系統）
        vectorization_service = SectionVectorizationService()
        
        if not created:
            # 更新時先刪除舊段落向量
            deleted = vectorization_service.delete_document_sections(
                source_table='protocol_guide',
                source_id=instance.id
            )
            logger.info(f"  🗑️  刪除舊段落向量: {deleted} 個")
        
        # 生成新段落向量
        result = vectorization_service.vectorize_document_sections(
            source_table='protocol_guide',
            source_id=instance.id,
            markdown_content=instance.content,
            document_title=instance.title
        )
        
        if result.get('success'):
            count = result.get('vectorized_count', 0)
            logger.info(f"  ✅ 段落向量{'生成' if created else '更新'}成功: {count} 個段落")
        else:
            error = result.get('error', 'Unknown error')
            logger.error(f"  ❌ 段落向量處理失敗: {error}")
            
    except Exception as e:
        logger.error(
            f"❌ Signal: Protocol Guide {instance.id} 向量處理失敗: {str(e)}",
            exc_info=True
        )


@receiver(post_delete, sender=ProtocolGuide)
def protocol_guide_post_delete(sender, instance, **kwargs):
    """
    Protocol Guide 刪除後自動刪除向量
    
    Args:
        sender: ProtocolGuide Model
        instance: 被刪除的實例（注意：此時 instance.id 可能已為 None）
    """
    from library.common.knowledge_base.section_vectorization_service import SectionVectorizationService
    from api.services.embedding_service import get_embedding_service
    
    # ⚠️ 重要：必須在刪除前保存 ID
    # 因為 post_delete 觸發時，instance.id 可能已經是 None
    # 如果需要在刪除前獲取 ID，應該使用 pre_delete signal
    
    # 這裡我們假設可以從 kwargs 或其他方式獲取 ID
    # 實際上應該使用 pre_delete signal 來保存 ID
    pass  # 暫時不實作，因為 ViewSet.perform_destroy 已處理


# 同樣的邏輯可以應用到 RVTGuide
@receiver(post_save, sender=RVTGuide)
def rvt_guide_post_save(sender, instance, created, **kwargs):
    """RVT Guide 儲存後自動生成/更新向量"""
    # 類似的實作...
    pass
```

**步驟 2：註冊 Signals**

```python
# backend/api/apps.py

from django.apps import AppConfig

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    
    def ready(self):
        """應用啟動時執行"""
        # 導入 signals（觸發 @receiver 裝飾器註冊）
        import api.signals  # noqa: F401
```

**步驟 3：重啟 Django**

```bash
docker restart ai-django
```

**步驟 4：測試驗證**

```python
# 在 Django shell 中測試
from api.models import ProtocolGuide

# 創建測試文檔
guide = ProtocolGuide.objects.create(
    title="Signal 測試",
    content="# 段落 1\n\n內容 1\n\n## 段落 2\n\n內容 2"
)

# 檢查向量是否生成
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT COUNT(*), 
               SUM(CASE WHEN document_id IS NOT NULL THEN 1 ELSE 0 END) as has_doc_id
        FROM document_section_embeddings 
        WHERE source_table='protocol_guide' AND source_id=%s
    """, [guide.id])
    result = cursor.fetchone()
    print(f"段落數量: {result[0]}, 有 document_id: {result[1]}")

# 預期結果：段落數量: 2, 有 document_id: 2
```

---

### 方案 2：修改測試腳本手動生成（臨時方案）

**適用場景**：
- 測試腳本
- 一次性數據導入
- 不想修改核心系統

**實作**：

```python
# test_new_protocol_guide_creation.py (修正版)

from api.models import ProtocolGuide
from library.common.knowledge_base.section_vectorization_service import SectionVectorizationService

# 創建文檔
guide = ProtocolGuide.objects.create(
    title="測試文檔",
    content="# 內容..."
)

# ✅ 手動觸發向量生成
vectorization_service = SectionVectorizationService()
result = vectorization_service.vectorize_document_sections(
    source_table='protocol_guide',
    source_id=guide.id,
    markdown_content=guide.content,
    document_title=guide.title
)

if result.get('success'):
    print(f"✅ 向量生成成功: {result.get('vectorized_count')} 個段落")
else:
    print(f"❌ 向量生成失敗: {result.get('error')}")
```

---

### 方案 3：批量修復現有資料（補救方案）

**場景**：已有大量資料沒有向量

**腳本**：

```python
# fix_missing_vectors.py

import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import ProtocolGuide
from library.common.knowledge_base.section_vectorization_service import SectionVectorizationService
from django.db import connection

def find_guides_without_vectors():
    """找出沒有段落向量的 Protocol Guides"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT pg.id, pg.title
            FROM protocol_guide pg
            LEFT JOIN document_section_embeddings dse
                ON dse.source_table = 'protocol_guide' AND dse.source_id = pg.id
            WHERE dse.id IS NULL
            ORDER BY pg.id;
        """)
        return cursor.fetchall()

def generate_vectors_for_guide(guide_id, title):
    """為特定 Guide 生成向量"""
    try:
        guide = ProtocolGuide.objects.get(id=guide_id)
        
        vectorization_service = SectionVectorizationService()
        result = vectorization_service.vectorize_document_sections(
            source_table='protocol_guide',
            source_id=guide.id,
            markdown_content=guide.content,
            document_title=guide.title
        )
        
        if result.get('success'):
            print(f"  ✅ {guide_id}: {title} ({result.get('vectorized_count')} 段落)")
            return True
        else:
            print(f"  ❌ {guide_id}: {title} - {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"  ❌ {guide_id}: {title} - {str(e)}")
        return False

def main():
    print("🔍 搜尋沒有段落向量的 Protocol Guides...")
    missing = find_guides_without_vectors()
    
    if not missing:
        print("✅ 所有 Protocol Guides 都有段落向量")
        return
    
    print(f"📋 找到 {len(missing)} 個沒有向量的文檔\n")
    
    success_count = 0
    for guide_id, title in missing:
        if generate_vectors_for_guide(guide_id, title):
            success_count += 1
    
    print(f"\n✅ 完成：{success_count}/{len(missing)} 個文檔向量已生成")

if __name__ == '__main__':
    main()
```

**執行**：

```bash
docker cp fix_missing_vectors.py ai-django:/app/
docker exec ai-django python fix_missing_vectors.py
```

---

## 📊 方案比較

| 方案 | 優點 | 缺點 | 推薦度 |
|------|------|------|--------|
| **方案 1: Django Signals** | 自動化、統一、可靠 | 增加複雜度 | ⭐⭐⭐⭐⭐ |
| **方案 2: 手動生成** | 簡單、直接 | 容易遺忘、不一致 | ⭐⭐ |
| **方案 3: 批量修復** | 補救現有資料 | 治標不治本 | ⭐⭐⭐ (配合方案1) |

---

## ✅ 推薦行動計劃

### 短期（立即執行）

1. **運行批量修復腳本**（方案 3）
   - 修復現有所有沒有向量的 Protocol Guides
   - 確保搜尋功能正常

2. **測試透過 API 創建**
   - 驗證 API 創建的文檔有完整向量
   - 確認 `document_id` 正確生成

### 中期（本週內）

3. **實作 Django Signals**（方案 1）⭐
   - 創建 `backend/api/signals.py`
   - 實作 `post_save` signal 處理向量生成
   - 在 `apps.py` 中註冊
   - 完整測試（ORM 創建、更新、刪除）

4. **更新文檔**
   - 記錄 Signal 實作細節
   - 更新開發指南

### 長期（下個 Sprint）

5. **考慮性能優化**
   - 評估 Signal 對性能的影響
   - 可能改為非同步（Celery task）
   - 批量操作時禁用 Signal

6. **同步套用到其他 Assistant**
   - RVT Guide
   - Know Issue
   - 未來的新 Assistant

---

## 🎯 總結回答您的問題

**問**：「當建立了新的 Protocol Guide 或是修改，會可能沒有產生對應的欄位或資料，是嗎？這部份修改了嗎？」

**答**：

1. **是的，有這個問題**：
   - ✅ 透過 **API** 創建/修改：會自動生成向量
   - ❌ 透過 **ORM** 創建/修改：**不會**自動生成向量

2. **目前的狀態**：
   - ✅ 向量生成邏輯已修復（包含 document_id）
   - ✅ API 創建/修改正常工作
   - ❌ **ORM 創建/修改不會觸發（這是您發現的新問題）**

3. **建議的修復**：
   - ⭐ **實作 Django Signals**（永久解決）
   - 📦 **批量修復現有資料**（補救）
   - 📝 **更新開發流程**（透過 API 創建）

4. **優先級**：
   - 如果主要透過 API 使用：優先級中等
   - 如果需要 Django Admin 或批量導入：優先級高

---

**更新日期**：2025-11-11  
**文檔狀態**：✅ 完整分析 + 解決方案
