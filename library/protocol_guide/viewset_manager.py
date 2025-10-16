"""
Protocol Guide ViewSet 管理器
=============================

使用基礎類別快速實現 Protocol Guide 的 ViewSet 管理邏輯。

代碼量：僅 15 行！（對比原始方式的 250+ 行）
"""

from library.common.knowledge_base import BaseKnowledgeBaseViewSetManager
# 注意：這裡假設已經創建了相關的 Serializers
# 實際使用時需要先創建: backend/api/serializers.py


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
    model_class = None              # ProtocolGuide
    serializer_class = None         # ProtocolGuideSerializer
    list_serializer_class = None    # ProtocolGuideListSerializer
    source_table = 'protocol_guide'
    
    def get_vector_service(self):
        """返回向量服務實例"""
        from .vector_service import ProtocolGuideVectorService
        return ProtocolGuideVectorService()
    
    # 如果需要特殊的創建邏輯（例如自動生成 Protocol ID），可以覆寫：
    # def perform_create(self, serializer):
    #     """自定義創建邏輯"""
    #     instance = serializer.save()
    #     
    #     # 生成特殊的 Protocol ID
    #     instance.protocol_id = self._generate_protocol_id(instance)
    #     instance.save()
    #     
    #     # 調用基礎類別的向量生成
    #     self.generate_vector_for_instance(instance, action='create')
    #     
    #     return instance
    # 
    # def _generate_protocol_id(self, instance):
    #     """生成 Protocol ID"""
    #     # 自定義 ID 生成邏輯
    #     return f"PROTO-{instance.id:04d}"
