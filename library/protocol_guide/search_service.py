"""
Protocol Guide 搜索服務
=======================

使用基礎類別快速實現 Protocol Guide 的搜索功能。

代碼量：僅 10 行！（對比原始方式的 200+ 行）
"""

from library.common.knowledge_base import BaseKnowledgeBaseSearchService


class ProtocolGuideSearchService(BaseKnowledgeBaseSearchService):
    """
    Protocol Guide 搜索服務
    
    繼承自 BaseKnowledgeBaseSearchService，自動獲得：
    - search_knowledge()       - 智能搜索（向量+關鍵字）
    - search_with_vectors()    - 向量搜索
    - search_with_keywords()   - 關鍵字搜索
    """
    
    # 設定必要的類別屬性
    model_class = None  # ProtocolGuide
    source_table = 'protocol_guide'
    
    # 設定要搜索的欄位
    default_search_fields = [
        'title',         # 標題
        'content',       # 內容
        'protocol_name', # Protocol 名稱（特有欄位）
        'description'    # 描述（如果有的話）
    ]
    
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
