"""
Protocol Guide 搜索服務
=======================

使用基礎類別快速實現 Protocol Guide 的搜索功能。

代碼量：僅 10 行！（對比原始方式的 200+ 行）
"""

from library.common.knowledge_base import BaseKnowledgeBaseSearchService
from api.models import ProtocolGuide


class ProtocolGuideSearchService(BaseKnowledgeBaseSearchService):
    """
    Protocol Guide 搜索服務
    
    繼承自 BaseKnowledgeBaseSearchService，自動獲得：
    - search_knowledge()       - 智能搜索（向量+關鍵字）
    - search_with_vectors()    - 向量搜索
    - search_with_keywords()   - 關鍵字搜索
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
        from .vector_service import ProtocolGuideVectorService
        return ProtocolGuideVectorService()
    
    def search_with_vectors(self, query, limit=5):
        """
        使用向量進行搜索 (Protocol Guide 專用)
        
        覆寫基礎類別方法，使用通用的向量搜索服務
        """
        try:
            from api.services.embedding_service import get_embedding_service
            
            # 使用 1024 維模型進行向量搜索
            embedding_service = get_embedding_service('ultra_high')
            results = embedding_service.search_similar_documents(
                query=query,
                source_table=self.source_table,
                limit=limit,
                threshold=0.0,  # 在這裡不過濾，交給上層處理
                use_1024_table=True
            )
            
            # 補充完整的記錄內容
            formatted_results = []
            for result in results:
                try:
                    # 查詢實際的 Protocol Guide 記錄
                    item = self.model_class.objects.get(id=result['source_id'])
                    formatted_results.append({
                        'content': self._get_item_content(item),
                        'score': float(result['similarity_score']),
                        'title': item.title,
                        'metadata': {
                            'id': item.id,
                            'created_at': item.created_at.isoformat(),
                            'updated_at': item.updated_at.isoformat(),
                        }
                    })
                except self.model_class.DoesNotExist:
                    self.logger.warning(f"找不到 Protocol Guide ID: {result['source_id']}")
                    continue
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"向量搜索錯誤: {str(e)}")
            return []
    
    # 如果需要自定義搜索邏輯，可以覆寫：
    # def _get_item_content(self, item):
    #     """自定義內容獲取邏輯"""
    #     # 組合多個欄位作為搜索內容
    #     content_parts = [
    #         f"Protocol: {item.protocol_name}",
    #         f"Title: {item.title}",
    #         f"Content: {item.content}",
    #     ]
    #     return ' '.join(content_parts)
