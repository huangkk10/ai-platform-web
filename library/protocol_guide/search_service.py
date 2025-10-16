"""
Protocol Guide 搜索服務
=======================

使用基礎類別快速實現 Protocol Guide 的搜索功能。

✨ 重構後：代碼從 ~100 行減少至 ~30 行！
- 移除了 search_with_vectors 覆寫（現在使用基類的通用實現）
- 向量搜尋邏輯由 vector_search_helper 統一處理
- Protocol Guide 和 RVT Guide 使用相同的底層方法
"""

from library.common.knowledge_base import BaseKnowledgeBaseSearchService
from api.models import ProtocolGuide


class ProtocolGuideSearchService(BaseKnowledgeBaseSearchService):
    """
    Protocol Guide 搜索服務
    
    繼承自 BaseKnowledgeBaseSearchService，自動獲得：
    - search_knowledge()       - 智能搜索（向量+關鍵字）
    - search_with_vectors()    - 向量搜索 (使用通用 helper)
    - search_with_keywords()   - 關鍵字搜索
    
    ✅ 重構優勢：
    - 不需要覆寫 search_with_vectors()
    - 與 RVT Guide 使用相同的實現方式
    - 代碼簡潔，易於維護
    """
    
    # 設定必要的類別屬性
    model_class = ProtocolGuide
    source_table = 'protocol_guide'
    
    # 設定要搜索的欄位（簡化版，與 RVTGuide 一致）
    default_search_fields = [
        'title',    # 標題
        'content',  # 內容
    ]
    
    def __init__(self):
        super().__init__()
    
    def get_vector_service(self):
        """獲取向量服務（用於自動生成向量）"""
        from .vector_service import ProtocolGuideVectorService
        return ProtocolGuideVectorService()
    
    # 可選：如果需要自定義內容格式化邏輯，可以覆寫此方法
    # def _get_item_content(self, item):
    #     """自定義內容獲取邏輯"""
    #     return f"標題: {item.title}\n內容: {item.content}"

