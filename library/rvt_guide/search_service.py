"""
RVT Guide 搜索服務

統一處理 RVT Guide 相關搜索功能：
- 向量搜索
- 關鍵字搜索  
- 混合搜索策略
- 備用搜索機制

減少 views.py 中搜索相關程式碼
"""

import logging

logger = logging.getLogger(__name__)


class RVTGuideSearchService:
    """RVT Guide 搜索服務 - 統一管理所有搜索功能"""
    
    def __init__(self):
        self.logger = logger
        self._vector_search_available = None
        self._database_search_service = None
    
    @property
    def vector_search_available(self):
        """檢查向量搜索是否可用"""
        if self._vector_search_available is None:
            try:
                # 檢查向量搜索服務是否可用
                from backend.api.services.embedding_service import search_rvt_guide_with_vectors
                self._vector_search_available = True
            except ImportError:
                self._vector_search_available = False
        return self._vector_search_available
    
    @property  
    def database_search_service(self):
        """獲取資料庫搜索服務"""
        if self._database_search_service is None:
            try:
                from ..data_processing.database_search import DatabaseSearchService
                self._database_search_service = DatabaseSearchService()
            except ImportError:
                self._database_search_service = None
        return self._database_search_service
    
    def search_knowledge(self, query_text, limit=5, threshold=0.1):
        """
        統一的 RVT Guide 知識搜索入口
        
        優先使用向量搜索，如果不可用則回退到關鍵字搜索
        
        Args:
            query_text: 查詢文本
            limit: 返回結果數量限制
            threshold: 向量搜索分數閾值
            
        Returns:
            list: 搜索結果列表
        """
        try:
            # 策略 1: 優先使用向量搜索
            if self.vector_search_available:
                try:
                    from backend.api.services.embedding_service import search_rvt_guide_with_vectors
                    search_results = search_rvt_guide_with_vectors(query_text, limit=limit, threshold=threshold)
                    self.logger.info(f"RVT Guide vector search results count: {len(search_results)}")
                    
                    # 如果向量搜索有結果，直接返回
                    if search_results:
                        return search_results
                    else:
                        self.logger.info("向量搜索無結果，回退到關鍵字搜索")
                        
                except Exception as e:
                    self.logger.error(f"向量搜索失敗，回退到關鍵字搜索: {e}")
            
            # 策略 2: 使用資料庫搜索服務
            if self.database_search_service:
                search_results = self.database_search_service.search_rvt_guide_knowledge(query_text, limit)
                self.logger.info(f"RVT Guide database search results count: {len(search_results)}")
                return search_results
            
            # 策略 3: 備用搜索實現
            else:
                self.logger.warning("DatabaseSearchService 不可用，使用備用實現")
                return self._fallback_search(query_text, limit)
                
        except Exception as e:
            self.logger.error(f"RVT Guide 搜索失敗: {str(e)}")
            return []
    
    def _fallback_search(self, query_text, limit=5):
        """
        備用搜索實現
        
        當所有高級搜索服務都不可用時使用
        """
        try:
            # 這裡可以實現簡單的備用搜索邏輯
            # 例如直接查詢資料庫
            return []
        except Exception as e:
            self.logger.error(f"備用搜索失敗: {str(e)}")
            return []
    
    def search_with_vectors(self, query_text, limit=5, threshold=0.1):
        """
        專門的向量搜索方法
        """
        if not self.vector_search_available:
            raise ValueError("向量搜索服務不可用")
        
        try:
            from backend.api.services.embedding_service import search_rvt_guide_with_vectors
            return search_rvt_guide_with_vectors(query_text, limit=limit, threshold=threshold)
        except Exception as e:
            self.logger.error(f"向量搜索異常: {str(e)}")
            raise
    
    def search_with_keywords(self, query_text, limit=5):
        """
        專門的關鍵字搜索方法
        """
        if not self.database_search_service:
            raise ValueError("資料庫搜索服務不可用")
        
        try:
            return self.database_search_service.search_rvt_guide_knowledge(query_text, limit)
        except Exception as e:
            self.logger.error(f"關鍵字搜索異常: {str(e)}")
            raise


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