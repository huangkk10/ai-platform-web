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
    
    def _format_content_for_embedding(self, instance):
        """
        格式化內容用於向量化（簡化版，與 RVTGuide 一致）
        
        組合標題和內容，加上圖片摘要
        """
        content_parts = [
            f"Title: {instance.title}",
            f"Content: {instance.content}",
        ]
        
        # 添加圖片摘要
        images_summary = instance.get_images_summary()
        if images_summary:
            content_parts.append(images_summary)
        
        return ' | '.join(content_parts)
    
    # 如果需要自定義向量化內容，可以覆寫：
    # def _get_content_for_vectorization(self, instance):
    #     """自定義向量化內容"""
    #     # 組合多個欄位作為向量化內容
    #     content_parts = [
    #         f"Protocol: {instance.protocol_name}",
    #         instance.title,
    #         instance.content,
    #     ]
    #     
    #     # 如果有測試步驟等特殊欄位
    #     if hasattr(instance, 'test_steps') and instance.test_steps:
    #         content_parts.append(f"Steps: {instance.test_steps}")
    #     
    #     return ' '.join(content_parts)
