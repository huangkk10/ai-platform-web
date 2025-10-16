"""
RVT Guide 搜索服務

統一處理 RVT Guide 相關搜索功能：
- 向量搜索
- 關鍵字搜索  
- 混合搜索策略
- 備用搜索機制

減少 views.py 中搜索相關程式碼

✨ 已遷移至新架構 - 繼承 BaseKnowledgeBaseSearchService
"""

import logging
from library.common.knowledge_base import BaseKnowledgeBaseSearchService
from api.models import RVTGuide

logger = logging.getLogger(__name__)


class RVTGuideSearchService(BaseKnowledgeBaseSearchService):
    """
    RVT Guide 搜索服務 - 繼承基礎搜索服務
    
    ✅ 已遷移至新架構，代碼從 149 行減少至 ~30 行
    
    繼承自 BaseKnowledgeBaseSearchService，自動獲得：
    - search_knowledge(): 智能搜索（向量+關鍵字）
    - search_with_vectors(): 向量搜索
    - search_with_keywords(): 關鍵字搜索
    - _format_search_results(): 結果格式化
    """
    
    # 設定必要屬性
    model_class = RVTGuide
    source_table = 'rvt_guide'
    default_search_fields = ['title', 'content']
    
    def __init__(self):
        super().__init__()
        self._database_search_service = None
    
    @property  
    def database_search_service(self):
        """
        獲取資料庫搜索服務（向後兼容）
        
        保留此方法以支援舊有功能
        """
        if self._database_search_service is None:
            try:
                from ..data_processing.database_search import DatabaseSearchService
                self._database_search_service = DatabaseSearchService()
            except ImportError:
                self._database_search_service = None
        return self._database_search_service


def search_rvt_guide_knowledge(query_text, limit=5):
    """
    向後兼容的搜索函數
    
    保持與原有 views.py 中函數的兼容性
    現在內部使用統一的搜索服務
    """
    try:
        search_service = RVTGuideSearchService()
        return search_service.search_knowledge(query_text, limit)
    except Exception as e:
        logger.error(f"RVT Guide 兼容搜索失敗: {str(e)}")
        return []