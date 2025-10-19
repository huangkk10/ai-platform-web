"""
Protocol Guide ViewSet 管理器
=============================

使用基礎類別快速實現 Protocol Guide 的 ViewSet 管理邏輯。

代碼量：僅 15 行！（對比原始方式的 250+ 行）
"""

from library.common.knowledge_base import BaseKnowledgeBaseViewSetManager
from api.models import ProtocolGuide
from api.serializers import ProtocolGuideSerializer, ProtocolGuideListSerializer


class ProtocolGuideViewSetManager(BaseKnowledgeBaseViewSetManager):
    """
    Protocol Guide ViewSet 管理器
    
    繼承自 BaseKnowledgeBaseViewSetManager，自動獲得：
    - get_serializer_class()      - 序列化器選擇
    - perform_create()            - 創建邏輯（含向量生成）
    - perform_update()            - 更新邏輯（含向量更新）
    - perform_destroy()           - 刪除邏輯（含向量刪除）
    - get_filtered_queryset()     - 過濾和搜索
    - get_statistics_data()       - 統計資料
    - handle_bulk_operations()    - 批量操作
    """
    
    # 設定必要的類別屬性
    model_class = ProtocolGuide
    source_table = 'protocol_guide'
    
    def __init__(self):
        # 延遲導入避免循環導入
        self.serializer_class = ProtocolGuideSerializer
        self.list_serializer_class = ProtocolGuideListSerializer
        super().__init__()
    
    def get_vector_service(self):
        """返回向量服務實例"""
        from .vector_service import ProtocolGuideVectorService
        return ProtocolGuideVectorService()
    
    def perform_create(self, serializer):
        """
        創建 Protocol Guide 時自動生成段落向量
        
        流程：
        1. 保存實例到資料庫
        2. 生成整篇文檔向量（舊系統）
        3. 生成段落向量（新系統）
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 1. 保存實例
        instance = serializer.save()
        
        # 2. 生成整篇文檔向量（使用基礎類別）
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
                metadata={
                    'title': instance.title,
                    'protocol_name': instance.protocol_name,
                    'version': instance.version
                }
            )
            logger.info(f"✅ Protocol Guide {instance.id} 段落向量生成成功 ({section_count} 個段落)")
        except Exception as e:
            logger.error(f"❌ 段落向量生成失敗: {str(e)}")
        
        return instance
    
    def perform_update(self, serializer):
        """
        更新 Protocol Guide 時自動更新段落向量
        
        流程：
        1. 保存更新到資料庫
        2. 更新整篇文檔向量（舊系統）
        3. 刪除舊段落向量
        4. 重新生成新段落向量（新系統）
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 1. 保存更新
        instance = serializer.save()
        
        # 2. 更新整篇文檔向量（使用基礎類別）
        try:
            self.generate_vector_for_instance(instance, action='update')
            logger.info(f"✅ Protocol Guide {instance.id} 整篇文檔向量更新成功")
        except Exception as e:
            logger.error(f"❌ 整篇文檔向量更新失敗: {str(e)}")
        
        # 3. 刪除舊段落向量並重新生成
        try:
            from library.common.knowledge_base.section_vectorization_service import SectionVectorizationService
            
            vectorization_service = SectionVectorizationService()
            
            # 刪除舊向量
            vectorization_service.delete_document_sections(
                source_table='protocol_guide',
                source_id=instance.id
            )
            
            # 重新生成
            section_count = vectorization_service.vectorize_document_sections(
                source_table='protocol_guide',
                source_id=instance.id,
                markdown_content=instance.content,
                metadata={
                    'title': instance.title,
                    'protocol_name': instance.protocol_name,
                    'version': instance.version
                }
            )
            logger.info(f"✅ Protocol Guide {instance.id} 段落向量更新成功 ({section_count} 個段落)")
        except Exception as e:
            logger.error(f"❌ 段落向量更新失敗: {str(e)}")
        
        return instance
    
    def perform_destroy(self, instance):
        """
        刪除 Protocol Guide 時同時刪除段落向量
        
        流程：
        1. 刪除整篇文檔向量（舊系統）
        2. 刪除所有段落向量（新系統）
        3. 刪除實例
        """
        import logging
        logger = logging.getLogger(__name__)
        
        guide_id = instance.id
        
        # 1. 刪除整篇文檔向量
        try:
            vector_service = self.get_vector_service()
            vector_service.delete_vector(guide_id)
            logger.info(f"✅ Protocol Guide {guide_id} 整篇文檔向量刪除成功")
        except Exception as e:
            logger.error(f"❌ 整篇文檔向量刪除失敗: {str(e)}")
        
        # 2. 刪除段落向量
        try:
            from library.common.knowledge_base.section_vectorization_service import SectionVectorizationService
            
            vectorization_service = SectionVectorizationService()
            vectorization_service.delete_document_sections(
                source_table='protocol_guide',
                source_id=guide_id
            )
            logger.info(f"✅ Protocol Guide {guide_id} 段落向量刪除成功")
        except Exception as e:
            logger.error(f"❌ 段落向量刪除失敗: {str(e)}")
        
        # 3. 刪除實例
        instance.delete()
