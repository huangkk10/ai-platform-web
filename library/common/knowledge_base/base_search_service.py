"""
知識庫搜索服務基礎類別
======================

提供統一的搜索邏輯，包括向量搜索和關鍵字搜索。
"""

import logging
from abc import ABC

logger = logging.getLogger(__name__)


class BaseKnowledgeBaseSearchService(ABC):
    """
    知識庫搜索服務基礎類別
    
    子類需要設定的屬性：
    - model_class: Django Model 類別
    - source_table: 資料來源表名
    - default_search_fields: 預設搜索欄位列表
    
    使用範例：
    ```python
    class ProtocolGuideSearchService(BaseKnowledgeBaseSearchService):
        model_class = ProtocolGuide
        source_table = 'protocol_guide'
        default_search_fields = ['title', 'content', 'protocol_name']
    ```
    """
    
    # 子類必須設定這些屬性
    model_class = None
    source_table = None
    default_search_fields = ['title', 'content']
    
    def __init__(self):
        self.logger = logger
        self._validate_attributes()
    
    def _validate_attributes(self):
        """驗證必要屬性是否已設定"""
        if self.model_class is None:
            raise NotImplementedError(f"{self.__class__.__name__} must define 'model_class' attribute")
        if self.source_table is None:
            raise NotImplementedError(f"{self.__class__.__name__} must define 'source_table' attribute")
    
    def search_knowledge(self, query, limit=5, use_vector=True):
        """
        搜索知識庫
        
        智能搜索策略：
        1. 優先嘗試向量搜索
        2. 如果向量搜索失敗或結果不足，使用關鍵字搜索
        3. 合併並去重結果
        """
        try:
            results = []
            
            # 嘗試向量搜索
            if use_vector:
                try:
                    vector_results = self.search_with_vectors(query, limit)
                    if vector_results:
                        results.extend(vector_results)
                        self.logger.info(f"向量搜索返回 {len(vector_results)} 條結果")
                except Exception as e:
                    self.logger.warning(f"向量搜索失敗: {str(e)}")
            
            # 如果結果不足，使用關鍵字搜索補充
            if len(results) < limit:
                remaining = limit - len(results)
                keyword_results = self.search_with_keywords(query, remaining)
                
                # 去重（避免重複的結果）
                existing_ids = {r.get('metadata', {}).get('id') for r in results}
                for kr in keyword_results:
                    kr_id = kr.get('metadata', {}).get('id')
                    if kr_id not in existing_ids:
                        results.append(kr)
                        existing_ids.add(kr_id)
                
                self.logger.info(f"關鍵字搜索補充 {len(keyword_results)} 條結果")
            
            return results[:limit]
            
        except Exception as e:
            self.logger.error(f"搜索失敗: {str(e)}")
            return []
    
    def search_with_vectors(self, query, limit=5):
        """
        使用向量進行搜索 (通用實現 - 已重構)
        
        ✨ 重構亮點：
        - 使用通用的 vector_search_helper 模組
        - 所有知識庫共用此實現
        - 子類無需覆寫，除非有特殊邏輯
        
        子類可以通過覆寫 _get_item_content() 來自定義內容格式化
        """
        try:
            from .vector_search_helper import search_with_vectors_generic
            
            # 調用通用向量搜尋 helper
            results = search_with_vectors_generic(
                query=query,
                model_class=self.model_class,
                source_table=self.source_table,
                limit=limit,
                threshold=0.0,  # 不在這裡過濾，交給上層 (search_knowledge) 處理
                use_1024=True,  # 預設使用 1024 維向量
                content_formatter=self._get_item_content  # 傳入子類的內容格式化方法
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"向量搜索錯誤: {str(e)}")
            return []
    
    def search_with_keywords(self, query, limit=5):
        """
        使用關鍵字進行搜索
        
        基於資料庫的關鍵字搜索
        """
        try:
            from django.db.models import Q
            
            # 構建搜索條件
            q_objects = Q()
            for field in self.default_search_fields:
                if hasattr(self.model_class, field):
                    q_objects |= Q(**{f"{field}__icontains": query})
            
            # 執行搜索
            items = self.model_class.objects.filter(q_objects)[:limit]
            
            results = []
            for item in items:
                results.append(self._format_item_to_result(item))
            
            return results
            
        except Exception as e:
            self.logger.error(f"關鍵字搜索錯誤: {str(e)}")
            return []
    
    def _format_search_results(self, raw_results):
        """
        格式化搜索結果為統一格式
        """
        formatted_results = []
        
        for result in raw_results:
            formatted_results.append({
                'content': result.get('content', ''),
                'score': result.get('score', 0.0),
                'title': result.get('title', ''),
                'metadata': result.get('metadata', {})
            })
        
        return formatted_results
    
    def _format_item_to_result(self, item):
        """
        將資料庫記錄格式化為搜索結果
        """
        return {
            'content': self._get_item_content(item),
            'score': 0.5,  # 關鍵字搜索給予固定分數
            'title': getattr(item, 'title', str(item)),
            'metadata': {
                'id': item.id,
                'created_at': item.created_at.isoformat() if hasattr(item, 'created_at') else None,
                'updated_at': item.updated_at.isoformat() if hasattr(item, 'updated_at') else None,
            }
        }
    
    def _get_item_content(self, item):
        """
        獲取記錄的搜索內容
        
        子類可以覆寫此方法來自定義內容獲取邏輯
        """
        if hasattr(item, 'get_search_content'):
            return item.get_search_content()
        elif hasattr(item, 'content'):
            return item.content
        else:
            return str(item)
