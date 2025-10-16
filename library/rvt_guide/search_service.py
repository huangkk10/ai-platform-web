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
    default_search_fields = ['title', 'content', 'issue_type', 'category']
    
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
    
    def _get_item_content(self, item):
        """
        覆寫父類方法 - 自定義 RVT Guide 內容獲取邏輯
        """
        if hasattr(item, 'get_search_content'):
            return item.get_search_content()
        
        # RVT Guide 特定內容組合
        parts = []
        if hasattr(item, 'title') and item.title:
            parts.append(f"標題: {item.title}")
        if hasattr(item, 'issue_type') and item.issue_type:
            parts.append(f"問題類型: {item.issue_type}")
        if hasattr(item, 'category') and item.category:
            parts.append(f"分類: {item.category}")
        if hasattr(item, 'content') and item.content:
            parts.append(f"內容: {item.content}")
        
        return "\n".join(parts) if parts else str(item)


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