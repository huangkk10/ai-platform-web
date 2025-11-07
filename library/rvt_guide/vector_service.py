"""
RVT Guide 向量服務

統一處理 RVT Guide 向量相關功能：
- 向量生成
- 向量存儲
- 向量更新
- 向量搜索

減少 views.py 中向量處理相關程式碼

✨ 已遷移至新架構 - 繼承 BaseKnowledgeBaseVectorService
"""

import logging
from library.common.knowledge_base import BaseKnowledgeBaseVectorService
from api.models import RVTGuide

logger = logging.getLogger(__name__)


class RVTGuideVectorService(BaseKnowledgeBaseVectorService):
    """
    RVT Guide 向量服務 - 繼承基礎向量服務
    
    ✅ 已遷移至新架構，代碼從 253 行減少至 ~40 行
    
    繼承自 BaseKnowledgeBaseVectorService，自動獲得：
    - generate_and_store_vector(): 生成並存儲向量
    - delete_vector(): 刪除向量
    - batch_generate_vectors(): 批量生成向量
    - rebuild_all_vectors(): 重建所有向量
    """
    
    # 設定必要屬性
    source_table = 'rvt_guide'
    model_class = RVTGuide
    
    def _get_title_for_vectorization(self, instance):
        """獲取標題（RVT Guide 有 title 欄位）"""
        return instance.title if hasattr(instance, 'title') else ""
    
    def _get_content_for_vectorization(self, instance):
        """
        獲取內容（不包含標題，因為標題已分開處理）
        
        包含內容和圖片摘要
        
        Args:
            instance: RVTGuide 實例
            
        Returns:
            str: 格式化後的內容（不含標題）
        """
        content_parts = []
        
        # 添加內容
        if hasattr(instance, 'content') and instance.content:
            content_parts.append(instance.content)
        
        # 添加圖片摘要
        if hasattr(instance, 'get_images_summary'):
            images_summary = instance.get_images_summary()
            if images_summary:
                content_parts.append(images_summary)
        
        return ' | '.join(content_parts) if content_parts else ""