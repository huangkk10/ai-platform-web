"""
Protocol Guide 向量服務
=======================

使用基礎類別快速實現 Protocol Guide 的向量處理功能。

代碼量：僅 8 行！（對比原始方式的 150+ 行）
"""

from library.common.knowledge_base import BaseKnowledgeBaseVectorService
from api.models import ProtocolGuide


class ProtocolGuideVectorService(BaseKnowledgeBaseVectorService):
    """
    Protocol Guide 向量服務
    
    繼承自 BaseKnowledgeBaseVectorService，自動獲得：
    - generate_and_store_vector()  - 生成並存儲向量
    - delete_vector()              - 刪除向量
    - batch_generate_vectors()     - 批量生成向量
    """
    
    # 設定必要的類別屬性
    source_table = 'protocol_guide'
    model_class = ProtocolGuide
    
    def _get_title_for_vectorization(self, instance):
        """獲取標題（Protocol Guide 有 title 欄位）"""
        return instance.title if hasattr(instance, 'title') else ""
    
    def _get_content_for_vectorization(self, instance):
        """
        獲取內容（不包含標題，因為標題已分開處理）
        
        包含內容和圖片摘要
        """
        content_parts = []
        
        # 添加內容
        if hasattr(instance, 'content') and instance.content:
            content_parts.append(instance.content)
        
        # 添加圖片摘要
        if hasattr(instance, 'get_images_summary'):
            images_summary = instance.get_images_summary()
            if images_summary:
                content_parts.append(images_summary)
        
        return ' | '.join(content_parts) if content_parts else ""
