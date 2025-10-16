"""
知識庫向量服務基礎類別
======================

提供統一的向量生成、存儲和刪除邏輯。
"""

import logging
from abc import ABC

logger = logging.getLogger(__name__)


class BaseKnowledgeBaseVectorService(ABC):
    """
    知識庫向量服務基礎類別
    
    子類需要設定的屬性：
    - source_table: 資料來源表名
    - model_class: Django Model 類別
    
    使用範例：
    ```python
    class ProtocolGuideVectorService(BaseKnowledgeBaseVectorService):
        source_table = 'protocol_guide'
        model_class = ProtocolGuide
    ```
    """
    
    # 子類必須設定這些屬性
    source_table = None
    model_class = None
    
    def __init__(self):
        self.logger = logger
        self._validate_attributes()
    
    def _validate_attributes(self):
        """驗證必要屬性是否已設定"""
        if self.source_table is None:
            raise NotImplementedError(f"{self.__class__.__name__} must define 'source_table' attribute")
        if self.model_class is None:
            raise NotImplementedError(f"{self.__class__.__name__} must define 'model_class' attribute")
    
    def generate_and_store_vector(self, instance, action='create'):
        """
        為實例生成並存儲向量
        
        Returns:
            bool: 是否成功
        """
        try:
            # 獲取 embedding 服務
            service = self._get_embedding_service()
            if not service:
                return False
            
            # 獲取要向量化的內容
            content = self._get_content_for_vectorization(instance)
            if not content:
                self.logger.warning(f"實例 {instance.id} 沒有可向量化的內容")
                return False
            
            # 生成向量
            success = service.generate_and_store_embedding(
                source_table=self.source_table,
                source_id=instance.id,
                content=content,
                use_1024_table=True  # 預設使用 1024 維向量
            )
            
            if success:
                self.logger.info(f"✅ 向量生成成功: {self.source_table} ID {instance.id}")
            else:
                self.logger.error(f"❌ 向量生成失敗: {self.source_table} ID {instance.id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"向量生成異常: {str(e)}")
            return False
    
    def delete_vector(self, instance):
        """
        刪除實例的向量資料
        
        Returns:
            bool: 是否成功
        """
        try:
            service = self._get_embedding_service()
            if not service:
                return False
            
            # 刪除 1024 維向量
            success_1024 = service.delete_document_embedding(
                source_table=self.source_table,
                source_id=instance.id,
                use_1024_table=True
            )
            
            # 刪除 768 維向量（備用）
            success_768 = service.delete_document_embedding(
                source_table=self.source_table,
                source_id=instance.id,
                use_1024_table=False
            )
            
            if success_1024 or success_768:
                self.logger.info(f"✅ 向量刪除成功: {self.source_table} ID {instance.id}")
                return True
            else:
                self.logger.warning(f"⚠️ 未找到向量資料: {self.source_table} ID {instance.id}")
                return False
                
        except Exception as e:
            self.logger.error(f"向量刪除異常: {str(e)}")
            return False
    
    def batch_generate_vectors(self, queryset):
        """
        批量生成向量
        
        Returns:
            dict: 包含成功和失敗數量的統計
        """
        total = queryset.count()
        success_count = 0
        failed_count = 0
        
        self.logger.info(f"開始批量生成向量: {self.source_table}, 總數: {total}")
        
        for instance in queryset:
            if self.generate_and_store_vector(instance, action='batch'):
                success_count += 1
            else:
                failed_count += 1
        
        self.logger.info(f"批量生成完成: 成功 {success_count}, 失敗 {failed_count}")
        
        return {
            'total': total,
            'success': success_count,
            'failed': failed_count
        }
    
    def _get_embedding_service(self):
        """
        獲取 embedding 服務實例
        """
        try:
            from api.services.embedding_service import get_embedding_service
            return get_embedding_service()
        except Exception as e:
            self.logger.error(f"無法獲取 embedding 服務: {str(e)}")
            return None
    
    def _get_content_for_vectorization(self, instance):
        """
        獲取實例的內容用於向量化
        
        子類可以覆寫此方法來自定義內容獲取邏輯
        """
        # 優先使用 get_search_content 方法
        if hasattr(instance, 'get_search_content'):
            return instance.get_search_content()
        
        # 否則組合標題和內容
        content_parts = []
        
        if hasattr(instance, 'title') and instance.title:
            content_parts.append(instance.title)
        
        if hasattr(instance, 'content') and instance.content:
            content_parts.append(instance.content)
        
        return ' '.join(content_parts) if content_parts else str(instance)
