"""
Protocol Guide API 處理器
========================

使用基礎類別快速實現 Protocol Guide 的所有 API 端點。

代碼量：僅 15 行！（對比原始方式的 300+ 行）
"""

from library.common.knowledge_base import BaseKnowledgeBaseAPIHandler
from api.models import ProtocolGuide


class ProtocolGuideAPIHandler(BaseKnowledgeBaseAPIHandler):
    """
    Protocol Guide API 處理器
    
    繼承自 BaseKnowledgeBaseAPIHandler，自動獲得：
    - handle_dify_search_api()  - Dify 知識庫搜索
    - handle_chat_api()         - 聊天 API
    - handle_config_api()       - 配置信息 API
    """
    
    # 設定必要的類別屬性
    knowledge_id = 'protocol_guide_db'      # Dify 知識庫 ID
    config_key = 'protocol_guide'           # 配置鍵名
    source_table = 'protocol_guide'         # 資料表名
    model_class = ProtocolGuide             # Model 類別
    
    @classmethod
    def get_search_service(cls):
        """返回搜索服務實例"""
        from .search_service import ProtocolGuideSearchService
        return ProtocolGuideSearchService()
    
    # 如果需要自定義邏輯，可以覆寫方法
    # 例如：
    # @classmethod
    # def perform_search(cls, query, limit=5):
    #     """自定義搜索邏輯"""
    #     # 實現特殊搜索邏輯
    #     pass
