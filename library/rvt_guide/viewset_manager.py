"""
RVT Guide ViewSet 管理器
=============================

使用基礎類別快速實現 RVT Guide 的 ViewSet 管理邏輯。

✨ 已遷移至新架構，代碼從 265 行減少至 ~40 行（-85%）
"""

from library.common.knowledge_base import BaseKnowledgeBaseViewSetManager
from api.models import RVTGuide


class RVTGuideViewSetManager(BaseKnowledgeBaseViewSetManager):
    """
    RVT Guide ViewSet 管理器
    
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
    model_class = RVTGuide
    source_table = 'rvt_guide'
    
    def __init__(self):
        # 延遲導入避免循環導入
        from api.serializers import RVTGuideSerializer, RVTGuideListSerializer
        self.serializer_class = RVTGuideSerializer
        self.list_serializer_class = RVTGuideListSerializer
        super().__init__()
    
    def get_vector_service(self):
        """返回向量服務實例"""
        from .vector_service import RVTGuideVectorService
        return RVTGuideVectorService()
