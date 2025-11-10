"""
Django Signals for Automatic Vector Generation
===============================================

當 Model 儲存或刪除時，自動觸發向量生成/刪除。

支援的 Models:
- ProtocolGuide: Protocol Assistant 知識庫
- RVTGuide: RVT Assistant 知識庫
- KnowIssue: Know Issue 知識庫

優點：
- 無論透過 API、Django Admin、ORM 創建，都會自動生成向量
- 統一處理邏輯，避免遺漏
- 符合 Django 最佳實踐
"""

from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from api.models import ProtocolGuide, RVTGuide, KnowIssue
import logging

logger = logging.getLogger(__name__)


# ==================== Protocol Guide Signals ====================

@receiver(post_save, sender=ProtocolGuide)
def protocol_guide_post_save(sender, instance, created, **kwargs):
    """
    Protocol Guide 儲存後自動生成/更新向量
    
    觸發時機：
    - ORM create: ProtocolGuide.objects.create(...)
    - ORM update: guide.save()
    - Django Admin: 新增/編輯記錄
    - Management Command: 批量創建
    
    Args:
        sender: ProtocolGuide Model 類別
        instance: 儲存的實例
        created: True=新創建, False=更新
    """
    action = 'create' if created else 'update'
    logger.info(f"🔔 Signal 觸發: Protocol Guide {instance.id} {action}")
    
    try:
        # 延遲導入避免循環導入
        from library.common.knowledge_base.section_vectorization_service import SectionVectorizationService
        from api.services.embedding_service import get_embedding_service
        
        # 1. 生成/更新整篇文檔向量（舊系統，document_embeddings 表）
        try:
            embedding_service = get_embedding_service('ultra_high')
            content = f"Title: {instance.title}\n\nContent:\n{instance.content}"
            
            embedding_service.store_document_embedding(
                source_table='protocol_guide',
                source_id=instance.id,
                content=content,
                use_1024_table=True
            )
            logger.info(f"  ✅ 整篇文檔向量{'生成' if created else '更新'}成功")
        except Exception as e:
            logger.error(f"  ❌ 整篇文檔向量處理失敗: {str(e)}")
        
        # 2. 生成/更新段落向量（新系統，document_section_embeddings 表）
        try:
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
            logger.error(f"  ❌ 段落向量處理異常: {str(e)}", exc_info=True)
            
    except Exception as e:
        logger.error(
            f"❌ Signal: Protocol Guide {instance.id} 向量處理失敗: {str(e)}",
            exc_info=True
        )


# 使用 pre_delete 保存 ID（因為 post_delete 時 instance.id 可能為 None）
_protocol_guide_delete_cache = {}

@receiver(pre_delete, sender=ProtocolGuide)
def protocol_guide_pre_delete(sender, instance, **kwargs):
    """在刪除前保存 Guide ID"""
    _protocol_guide_delete_cache[id(instance)] = instance.id
    logger.info(f"🔔 Signal 觸發: Protocol Guide {instance.id} pre_delete (ID 已緩存)")


@receiver(post_delete, sender=ProtocolGuide)
def protocol_guide_post_delete(sender, instance, **kwargs):
    """
    Protocol Guide 刪除後自動刪除向量
    
    觸發時機：
    - ORM delete: guide.delete()
    - Django Admin: 刪除記錄
    - QuerySet delete: ProtocolGuide.objects.filter(...).delete()
    """
    # 從緩存中獲取 ID（因為 instance.id 可能已經是 None）
    guide_id = _protocol_guide_delete_cache.pop(id(instance), instance.id)
    
    if guide_id is None:
        logger.warning("❌ Signal: 無法獲取 Protocol Guide ID，跳過向量刪除")
        return
    
    logger.info(f"🔔 Signal 觸發: Protocol Guide {guide_id} post_delete")
    
    try:
        from library.common.knowledge_base.section_vectorization_service import SectionVectorizationService
        from api.services.embedding_service import get_embedding_service
        
        # 1. 刪除整篇文檔向量
        try:
            embedding_service = get_embedding_service('ultra_high')
            embedding_service.delete_document_embedding(
                source_table='protocol_guide',
                source_id=guide_id,
                use_1024_table=True
            )
            logger.info(f"  ✅ 整篇文檔向量刪除成功")
        except Exception as e:
            logger.error(f"  ❌ 整篇文檔向量刪除失敗: {str(e)}")
        
        # 2. 刪除段落向量
        try:
            vectorization_service = SectionVectorizationService()
            deleted = vectorization_service.delete_document_sections(
                source_table='protocol_guide',
                source_id=guide_id
            )
            logger.info(f"  ✅ 段落向量刪除成功: {deleted} 個")
        except Exception as e:
            logger.error(f"  ❌ 段落向量刪除失敗: {str(e)}")
        
    except Exception as e:
        logger.error(
            f"❌ Signal: Protocol Guide {guide_id} 向量刪除失敗: {str(e)}",
            exc_info=True
        )


# ==================== RVT Guide Signals ====================

@receiver(post_save, sender=RVTGuide)
def rvt_guide_post_save(sender, instance, created, **kwargs):
    """RVT Guide 儲存後自動生成/更新向量"""
    action = 'create' if created else 'update'
    logger.info(f"🔔 Signal 觸發: RVT Guide {instance.id} {action}")
    
    try:
        from library.common.knowledge_base.section_vectorization_service import SectionVectorizationService
        from api.services.embedding_service import get_embedding_service
        
        # 1. 生成/更新整篇文檔向量
        try:
            embedding_service = get_embedding_service('ultra_high')
            content = f"Title: {instance.title}\n\nContent:\n{instance.content}"
            
            embedding_service.store_document_embedding(
                source_table='rvt_guide',
                source_id=instance.id,
                content=content,
                use_1024_table=True
            )
            logger.info(f"  ✅ RVT Guide 整篇向量{'生成' if created else '更新'}成功")
        except Exception as e:
            logger.error(f"  ❌ RVT Guide 整篇向量處理失敗: {str(e)}")
        
        # 2. 生成/更新段落向量
        try:
            vectorization_service = SectionVectorizationService()
            
            if not created:
                deleted = vectorization_service.delete_document_sections(
                    source_table='rvt_guide',
                    source_id=instance.id
                )
                logger.info(f"  🗑️  RVT Guide 刪除舊段落向量: {deleted} 個")
            
            result = vectorization_service.vectorize_document_sections(
                source_table='rvt_guide',
                source_id=instance.id,
                markdown_content=instance.content,
                document_title=instance.title
            )
            
            if result.get('success'):
                count = result.get('vectorized_count', 0)
                logger.info(f"  ✅ RVT Guide 段落向量{'生成' if created else '更新'}成功: {count} 個")
            else:
                error = result.get('error', 'Unknown error')
                logger.error(f"  ❌ RVT Guide 段落向量處理失敗: {error}")
                
        except Exception as e:
            logger.error(f"  ❌ RVT Guide 段落向量處理異常: {str(e)}", exc_info=True)
            
    except Exception as e:
        logger.error(
            f"❌ Signal: RVT Guide {instance.id} 向量處理失敗: {str(e)}",
            exc_info=True
        )


_rvt_guide_delete_cache = {}

@receiver(pre_delete, sender=RVTGuide)
def rvt_guide_pre_delete(sender, instance, **kwargs):
    """在刪除前保存 Guide ID"""
    _rvt_guide_delete_cache[id(instance)] = instance.id
    logger.info(f"🔔 Signal 觸發: RVT Guide {instance.id} pre_delete (ID 已緩存)")


@receiver(post_delete, sender=RVTGuide)
def rvt_guide_post_delete(sender, instance, **kwargs):
    """RVT Guide 刪除後自動刪除向量"""
    guide_id = _rvt_guide_delete_cache.pop(id(instance), instance.id)
    
    if guide_id is None:
        logger.warning("❌ Signal: 無法獲取 RVT Guide ID，跳過向量刪除")
        return
    
    logger.info(f"🔔 Signal 觸發: RVT Guide {guide_id} post_delete")
    
    try:
        from library.common.knowledge_base.section_vectorization_service import SectionVectorizationService
        from api.services.embedding_service import get_embedding_service
        
        # 1. 刪除整篇文檔向量
        try:
            embedding_service = get_embedding_service('ultra_high')
            embedding_service.delete_document_embedding(
                source_table='rvt_guide',
                source_id=guide_id,
                use_1024_table=True
            )
            logger.info(f"  ✅ RVT Guide 整篇向量刪除成功")
        except Exception as e:
            logger.error(f"  ❌ RVT Guide 整篇向量刪除失敗: {str(e)}")
        
        # 2. 刪除段落向量
        try:
            vectorization_service = SectionVectorizationService()
            deleted = vectorization_service.delete_document_sections(
                source_table='rvt_guide',
                source_id=guide_id
            )
            logger.info(f"  ✅ RVT Guide 段落向量刪除成功: {deleted} 個")
        except Exception as e:
            logger.error(f"  ❌ RVT Guide 段落向量刪除失敗: {str(e)}")
        
    except Exception as e:
        logger.error(
            f"❌ Signal: RVT Guide {guide_id} 向量刪除失敗: {str(e)}",
            exc_info=True
        )


# ==================== Know Issue Signals ====================
# Note: Know Issue 使用舊的整篇文檔向量系統，不需要段落向量

@receiver(post_save, sender=KnowIssue)
def know_issue_post_save(sender, instance, created, **kwargs):
    """Know Issue 儲存後自動生成/更新向量"""
    action = 'create' if created else 'update'
    logger.info(f"🔔 Signal 觸發: Know Issue {instance.id} {action}")
    
    try:
        from api.services.embedding_service import get_embedding_service
        
        embedding_service = get_embedding_service('ultra_high')
        
        # Know Issue 只使用整篇文檔向量（舊系統）
        content = f"Issue ID: {instance.issue_id}\nTest Class: {instance.test_class.class_name if instance.test_class else ''}\nError Message: {instance.error_message}\nScript: {instance.script}"
        
        embedding_service.store_document_embedding(
            source_table='know_issue',
            source_id=instance.id,
            content=content,
            use_1024_table=True
        )
        
        logger.info(f"  ✅ Know Issue 向量{'生成' if created else '更新'}成功")
        
    except Exception as e:
        logger.error(
            f"❌ Signal: Know Issue {instance.id} 向量處理失敗: {str(e)}",
            exc_info=True
        )


_know_issue_delete_cache = {}

@receiver(pre_delete, sender=KnowIssue)
def know_issue_pre_delete(sender, instance, **kwargs):
    """在刪除前保存 Issue ID"""
    _know_issue_delete_cache[id(instance)] = instance.id
    logger.info(f"🔔 Signal 觸發: Know Issue {instance.id} pre_delete (ID 已緩存)")


@receiver(post_delete, sender=KnowIssue)
def know_issue_post_delete(sender, instance, **kwargs):
    """Know Issue 刪除後自動刪除向量"""
    issue_id = _know_issue_delete_cache.pop(id(instance), instance.id)
    
    if issue_id is None:
        logger.warning("❌ Signal: 無法獲取 Know Issue ID，跳過向量刪除")
        return
    
    logger.info(f"🔔 Signal 觸發: Know Issue {issue_id} post_delete")
    
    try:
        from api.services.embedding_service import get_embedding_service
        
        embedding_service = get_embedding_service('ultra_high')
        embedding_service.delete_document_embedding(
            source_table='know_issue',
            source_id=issue_id,
            use_1024_table=True
        )
        
        logger.info(f"  ✅ Know Issue 向量刪除成功")
        
    except Exception as e:
        logger.error(
            f"❌ Signal: Know Issue {issue_id} 向量刪除失敗: {str(e)}",
            exc_info=True
        )


# ==================== 工具函數 ====================

def disable_signals():
    """
    臨時禁用 signals（用於批量操作）
    
    使用方式：
    ```python
    from api.signals import disable_signals, enable_signals
    
    disable_signals()
    # 批量操作...
    ProtocolGuide.objects.bulk_create([...])
    enable_signals()
    ```
    """
    from django.db.models.signals import post_save, post_delete, pre_delete
    
    # Protocol Guide
    post_save.disconnect(protocol_guide_post_save, sender=ProtocolGuide)
    pre_delete.disconnect(protocol_guide_pre_delete, sender=ProtocolGuide)
    post_delete.disconnect(protocol_guide_post_delete, sender=ProtocolGuide)
    
    # RVT Guide
    post_save.disconnect(rvt_guide_post_save, sender=RVTGuide)
    pre_delete.disconnect(rvt_guide_pre_delete, sender=RVTGuide)
    post_delete.disconnect(rvt_guide_post_delete, sender=RVTGuide)
    
    # Know Issue
    post_save.disconnect(know_issue_post_save, sender=KnowIssue)
    pre_delete.disconnect(know_issue_pre_delete, sender=KnowIssue)
    post_delete.disconnect(know_issue_post_delete, sender=KnowIssue)
    
    logger.info("🔕 Signals 已禁用")


def enable_signals():
    """重新啟用 signals"""
    from django.db.models.signals import post_save, post_delete, pre_delete
    
    # Protocol Guide
    post_save.connect(protocol_guide_post_save, sender=ProtocolGuide)
    pre_delete.connect(protocol_guide_pre_delete, sender=ProtocolGuide)
    post_delete.connect(protocol_guide_post_delete, sender=ProtocolGuide)
    
    # RVT Guide
    post_save.connect(rvt_guide_post_save, sender=RVTGuide)
    pre_delete.connect(rvt_guide_pre_delete, sender=RVTGuide)
    post_delete.connect(rvt_guide_post_delete, sender=RVTGuide)
    
    # Know Issue
    post_save.connect(know_issue_post_save, sender=KnowIssue)
    pre_delete.connect(know_issue_pre_delete, sender=KnowIssue)
    post_delete.connect(know_issue_post_delete, sender=KnowIssue)
    
    logger.info("🔔 Signals 已啟用")
