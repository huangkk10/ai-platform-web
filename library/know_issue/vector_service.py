"""
Know Issue 向量服務
===================

負責 know_issue 表的向量生成和管理

功能：
- 為 know_issue 記錄生成 1024 維向量
- 存儲向量到 document_embeddings 表
- 支援向量更新和刪除
"""

from library.common.knowledge_base.base_vector_service import BaseKnowledgeBaseVectorService
from api.models import KnowIssue
import logging

logger = logging.getLogger(__name__)


class KnowIssueVectorService(BaseKnowledgeBaseVectorService):
    """
    Know Issue 向量服務
    
    繼承自 BaseKnowledgeBaseVectorService，提供：
    - generate_and_store_vector(): 生成並存儲向量
    - delete_vector(): 刪除向量
    - update_vector(): 更新向量
    """
    
    source_table = 'know_issue'
    model_class = KnowIssue
    
    def _format_content_for_embedding(self, instance):
        """
        格式化內容用於向量化
        
        將 Know Issue 的多個欄位組合成適合向量化的文本
        
        Args:
            instance: KnowIssue 實例
            
        Returns:
            格式化後的字串
        """
        content_parts = []
        
        # Issue ID (重要識別資訊)
        if instance.issue_id:
            content_parts.append(f"Issue ID: {instance.issue_id}")
        
        # 專案名稱
        if instance.project:
            content_parts.append(f"Project: {instance.project}")
        
        # 錯誤訊息（最重要的搜尋內容）
        if instance.error_message:
            content_parts.append(f"Error Message: {instance.error_message}")
        
        # 補充說明
        if instance.supplement:
            content_parts.append(f"Supplement: {instance.supplement}")
        
        # 相關腳本
        if instance.script:
            content_parts.append(f"Script: {instance.script}")
        
        # JIRA 號碼
        if instance.jira_number:
            content_parts.append(f"JIRA: {instance.jira_number}")
        
        # 測試類別
        if instance.test_class:
            content_parts.append(f"Test Class: {instance.test_class.name}")
        
        content = " | ".join(content_parts)
        
        logger.debug(f"📝 格式化 Know Issue {instance.issue_id} 用於向量化: {len(content)} 字元")
        
        return content
