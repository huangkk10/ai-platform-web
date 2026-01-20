"""
Know Issue 搜索服務
====================

專門用於搜尋 Protocol RAG 的已知問題資料庫 (know_issue 表)

功能：
- 向量搜尋：使用語義搜尋找到相關問題
- 關鍵字搜尋：基於錯誤訊息、Issue ID、專案名稱等欄位
- 混合搜尋：結合向量和關鍵字結果
"""

from library.common.knowledge_base import BaseKnowledgeBaseSearchService
from api.models import KnowIssue
import logging

logger = logging.getLogger(__name__)


class KnowIssueSearchService(BaseKnowledgeBaseSearchService):
    """
    Know Issue 搜索服務
    
    繼承自 BaseKnowledgeBaseSearchService，自動獲得：
    - search_knowledge()       - 智能搜索（向量+關鍵字）
    - search_with_vectors()    - 向量搜索
    - search_with_keywords()   - 關鍵字搜索
    
    特點：
    - 搜尋範圍：know_issue 表（已知問題資料庫）
    - 搜尋欄位：issue_id, error_message, project, script, supplement
    - 用途：Protocol RAG 聊天功能
    """
    
    # 設定必要的類別屬性
    model_class = KnowIssue
    source_table = 'know_issue'
    
    # 設定要搜索的欄位
    default_search_fields = [
        'issue_id',        # Issue ID (例如 "ULINK-001")
        'error_message',   # 錯誤訊息（主要搜尋欄位）
        'project',         # 專案名稱
        'script',          # 相關腳本
        'supplement',      # 補充說明
        'jira_number',     # JIRA 號碼
    ]
    
    def __init__(self):
        super().__init__()
        logger.info("✅ KnowIssueSearchService 初始化成功")
    
    def get_vector_service(self):
        """獲取向量服務（用於自動生成向量）"""
        from .vector_service import KnowIssueVectorService
        return KnowIssueVectorService()
    
    def _format_search_result(self, result: dict) -> dict:
        """
        格式化搜尋結果，使其更適合 Protocol RAG 使用
        
        Args:
            result: 原始搜尋結果
            
        Returns:
            格式化後的結果
        """
        # 基礎格式化（由父類別處理）
        formatted = super()._format_search_result(result)
        
        # 添加 Know Issue 特定的欄位
        if 'issue_id' in result:
            formatted['issue_id'] = result['issue_id']
        
        if 'project' in result:
            formatted['project'] = result['project']
        
        if 'jira_number' in result:
            formatted['jira_number'] = result['jira_number']
        
        if 'issue_type' in result:
            formatted['issue_type'] = result['issue_type']
        
        if 'status' in result:
            formatted['status'] = result['status']
        
        # 組合完整內容用於顯示
        content_parts = []
        
        if result.get('error_message'):
            content_parts.append(f"錯誤訊息：{result['error_message']}")
        
        if result.get('supplement'):
            content_parts.append(f"\n補充說明：{result['supplement']}")
        
        if result.get('script'):
            content_parts.append(f"\n相關腳本：{result['script']}")
        
        formatted['content'] = '\n'.join(content_parts)
        
        return formatted
